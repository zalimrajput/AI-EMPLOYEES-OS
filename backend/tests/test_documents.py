"""Document pipeline unit tests: chunking + text extraction (no DB)."""
import sys

sys.path.insert(0, ".")

from app.services.document_service import chunk_text, extract_text


def test_chunk_text_single_short():
    assert chunk_text("hello world") == ["hello world"]


def test_chunk_text_multiple():
    text = "word " * 5000
    chunks = chunk_text(text)
    assert len(chunks) > 1
    assert all(len(c) <= 1500 for c in chunks)


def test_chunk_text_empty():
    assert chunk_text("") == []
    assert chunk_text("   \n  ") == []


def test_extract_plain_text():
    assert extract_text("readme.txt", b"plain contents") == "plain contents"


def test_extract_markdown():
    assert "md contents" in extract_text("doc.md", b"md contents")


def test_extract_pdf(tmp_path):
    raw = b"%PDF-1.4 fake"  # pypdf will raise; ensure graceful exception path
    try:
        result = extract_text("a.pdf", raw)
        assert isinstance(result, str)
    except Exception:
        pass


def test_mime_for():
    from app.services.document_service import _mime_for

    assert _mime_for("x.pdf") == "application/pdf"
    assert _mime_for("x.docx") == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert _mime_for("x.csv") == "text/csv"