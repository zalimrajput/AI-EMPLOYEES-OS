"""OCR document intelligence: image + scanned-PDF text extraction.

Used as a fallback when native text extraction yields nothing (images,
scanned PDFs). Requires the Tesseract OCR binary at the OS level —
``pytesseract`` alone is not enough. If the binary is absent every function
degrades to a safe empty-string result so ingest pipelines never crash.
"""
import io
import logging
import os
import shutil
from functools import lru_cache

logger = logging.getLogger("app.services.ocr_service")

_MIN_PDF_TEXT_CHARS = 20  # below this we treat pypdf extraction as "scanned"

_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "tif", "tiff", "webp"}

_WINDOWS_CANDIDATES = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\Tesseract-OCR\tesseract.exe",
)


@lru_cache(maxsize=1)
def _find_tesseract_cmd() -> str | None:
    override = os.environ.get("TESSERACT_CMD") or os.environ.get("TESSERACT_EXE")
    if override and os.path.isfile(override):
        return override
    which = shutil.which("tesseract")
    if which:
        return which
    if os.name == "nt":
        for candidate in _WINDOWS_CANDIDATES:
            if os.path.isfile(candidate):
                return candidate
    return None


def tesseract_available() -> bool:
    """True when the Tesseract binary can be located and invoked."""
    cmd = _find_tesseract_cmd()
    if not cmd:
        return False
    try:
        import pytesseract

        pytesseract.pytesseract.tesseract_cmd = cmd
        return bool(pytesseract.get_tesseract_version())
    except Exception:  # noqa: BLE001
        return False


def _get_tesseract():
    try:
        import pytesseract

        cmd = _find_tesseract_cmd()
        if cmd:
            pytesseract.pytesseract.tesseract_cmd = cmd
        return pytesseract
    except ImportError:
        return None


def ocr_image(image_bytes: bytes) -> str:
    """Run OCR over raw image bytes; returns extracted text ("" on failure)."""
    tesseract = _get_tesseract()
    if tesseract is None:
        return ""
    try:
        from PIL import Image, ImageOps

        image = Image.open(io.BytesIO(image_bytes))
        image = ImageOps.exif_transpose(image).convert("L")
        text = tesseract.image_to_string(image, timeout=30)
        return (text or "").strip()
    except Exception:  # noqa: BLE001 - missing binary, corrupt image, etc.
        return ""


def extract_text_from_image(image_bytes: bytes) -> str:
    """Public API: OCR a single image. Returns "" when unusable."""
    return ocr_image(image_bytes)


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """OCR a scanned PDF: render each page to an image, then OCR it.

    PDF→image rendering uses PyMuPDF (bundles its own renderer; no poppler
    requirement). Returns "" if the binary is missing or rendering fails.
    """
    try:
        import pymupdf
    except ImportError:  # pragma: no cover - older PyMuPDF
        import fitz as pymupdf

    if not tesseract_available():
        return ""
    pages: list[str] = []
    try:
        with pymupdf.open(stream=pdf_bytes, filetype="pdf") as pdf:
            for page in pdf:
                pix = page.get_pixmap(dpi=200)
                pages.append(ocr_image(pix.tobytes("png")))
    except Exception:  # noqa: BLE001 - malformed PDF
        return ""
    return "\n\n".join(p for p in pages if p).strip()


def is_image_filename(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in _IMAGE_EXTENSIONS


def needs_ocr_fallback(text: str) -> bool:
    return len((text or "").strip()) < _MIN_PDF_TEXT_CHARS