"""OCR document intelligence tests.

Unit tests mock the tesseract call so the wiring/fallback logic runs without
an OS-level binary. E2E tests require a real Tesseract binary and skip
automatically when none is present.
"""
import io
import sys

sys.path.insert(0, ".")

import pytest

from app.services import document_service
from app.services.document_service import extract_text
from app.services.ocr_service import (
    extract_text_from_image,
    extract_text_from_pdf,
    is_image_filename,
    needs_ocr_fallback,
    tesseract_available,
)


class _FakeTesseract:
    def __init__(self, result="FAKE OCR TEXT"):
        self.result = result
        self.calls = 0

    def image_to_string(self, image, timeout=30):
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def _png_bytes():
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (80, 40), "white").save(buf, format="PNG")
    return buf.getvalue()


# ------------------------------------------------------------- unit (mocked)


def test_ocr_image_returns_text(monkeypatch):
    fake = _FakeTesseract()
    monkeypatch.setattr("app.services.ocr_service._get_tesseract", lambda: fake)
    assert extract_text_from_image(_png_bytes()) == "FAKE OCR TEXT"
    assert fake.calls == 1


def test_ocr_image_empty_on_failure(monkeypatch):
    fake = _FakeTesseract(result=RuntimeError("binary broken"))
    monkeypatch.setattr("app.services.ocr_service._get_tesseract", lambda: fake)
    assert extract_text_from_image(_png_bytes()) == ""


def test_ocr_image_empty_when_package_missing(monkeypatch):
    monkeypatch.setattr("app.services.ocr_service._get_tesseract", lambda: None)
    assert extract_text_from_image(b"whatever") == ""


def test_tesseract_not_available_without_binary(monkeypatch):
    monkeypatch.setattr("app.services.ocr_service._find_tesseract_cmd", lambda: None)
    assert tesseract_available() is False


def test_needs_ocr_fallback_threshold():
    assert needs_ocr_fallback("") is True
    assert needs_ocr_fallback("   \n ") is True
    assert needs_ocr_fallback("tiny") is True
    assert needs_ocr_fallback(None) is True
    assert (
        needs_ocr_fallback(
            "This is a regular text based PDF document with real content."
        )
        is False
    )


def test_is_image_filename():
    assert is_image_filename("scan.PNG") is True
    assert is_image_filename("scan.jpeg") is True
    assert is_image_filename("doc.pdf") is False
    assert is_image_filename("doc.txt") is False


def test_image_document_triggers_ocr(monkeypatch):
    captured = {}

    def fake(raw):
        captured["raw"] = raw
        return "OCR RESULT FROM IMAGE"

    monkeypatch.setattr(
        "app.services.document_service._ocr_text_from_image_bytes", fake
    )
    assert extract_text("scan.png", b"image bytes") == "OCR RESULT FROM IMAGE"
    assert captured["raw"] == b"image bytes"


# ----------------------------------------------------------------- fallback


def _text_pdf_bytes():
    from io import BytesIO

    from reportlab.pdfgen import canvas

    buf = BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(
        50,
        700,
        "This is a regular text based PDF document for testing OCR fallback.",
    )
    c.save()
    return buf.getvalue()


def _blank_pdf_bytes():
    from io import BytesIO

    from reportlab.pdfgen import canvas

    buf = BytesIO()
    canvas.Canvas(buf).save()
    return buf.getvalue()


def test_text_pdf_is_not_ocr_fed(monkeypatch):
    def unexpected(*args, **kwargs):
        raise AssertionError("OCR must not run for a normal text PDF")

    monkeypatch.setattr(
        "app.services.document_service._ocr_text_from_pdf_bytes", unexpected
    )
    result = extract_text("doc.pdf", _text_pdf_bytes())
    assert "regular text based PDF document" in result


def test_scanned_pdf_triggers_ocr(monkeypatch):
    called = {"count": 0}

    def fake(raw):
        called["count"] += 1
        return "SCANNED PDF OCR RESULT"

    monkeypatch.setattr(
        "app.services.document_service._ocr_text_from_pdf_bytes", fake
    )
    assert extract_text("scan.pdf", _blank_pdf_bytes()) == "SCANNED PDF OCR RESULT"
    assert called["count"] == 1


# ------------------------------------------------------------ e2e (real OCR)


e2e = pytest.mark.skipif(
    not tesseract_available(), reason="Tesseract binary not available"
)


def _make_text_image_bytes(text):
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("L", (260, 70), "white")
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 34)
    except Exception:
        font = ImageFont.load_default()
    d.text((14, 14), text, fill="black", font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _scanned_pdf_bytes(text):
    import pymupdf

    img_bytes = _make_text_image_bytes(text)
    with pymupdf.open() as pdf:
        page = pdf.new_page(width=520, height=140)
        page.insert_image(page.rect, stream=img_bytes)
        return pdf.tobytes()


@e2e
def test_e2e_image_ocr_roundtrip():
    result = extract_text_from_image(_make_text_image_bytes("TEST123"))
    assert "TEST123" in result


@e2e
def test_e2e_scanned_pdf_ocr_roundtrip():
    result = extract_text_from_pdf(_scanned_pdf_bytes("SCANME"))
    assert "SCANME" in result


@e2e
@pytest.mark.db
def test_e2e_ingest_document_ocr_fallback(db, monkeypatch):
    import uuid

    from sqlalchemy import text

    monkeypatch.setattr(
        "app.services.document_service.embed", lambda chunks: []
    )

    from app.models.document import Document
    from app.models.organization import Organization
    from app.services.document_service import ingest_document

    org = Organization(
        name="OCR Org",
        slug=f"ocr-{uuid.uuid4().hex[:10]}",
        settings={},
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    try:
        result = ingest_document(
            db,
            organization_id=org.id,
            uploaded_by=None,
            filename="scanned-invoice.pdf",
            raw=_scanned_pdf_bytes("INGEST123"),
            title="Scanned Invoice",
        )
        stored = (
            db.query(Document)
            .filter(Document.id == result["document_id"])
            .first()
        )
        assert stored is not None
        assert "INGEST123" in (stored.extracted_text or "")
    finally:
        db.execute(
            text("DELETE FROM knowledge_articles WHERE organization_id = :id"),
            {"id": org.id},
        )
        db.execute(text("DELETE FROM documents WHERE organization_id = :id"), {"id": org.id})
        db.execute(text("DELETE FROM organizations WHERE id = :id"), {"id": org.id})
        db.commit()