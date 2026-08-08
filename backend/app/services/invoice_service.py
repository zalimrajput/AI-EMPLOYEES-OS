"""Invoice & quotation business logic: line-item totals and PDF generation.

Routers stay thin — any non-trivial computation for documents lives here.
PDF generation is invoked by the dedicated PDF endpoints in the finance /
sales routers; the produced bytes are streamed straight back to the caller.
"""
import io
from decimal import Decimal
from pathlib import Path
from urllib.parse import unquote
from uuid import UUID
from typing import TYPE_CHECKING

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.models.invoice import Invoice, InvoiceItem
from app.models.organization import Organization
from app.models.organization_settings import OrganizationSettings
from app.models.quotation import Quotation, QuotationItem
from app.repositories.invoice_repository import compute_invoice_totals

if TYPE_CHECKING:
    from reportlab.pdfgen.canvas import Canvas


_LOGO_MAX_WIDTH = 26 * mm
_LOGO_MAX_HEIGHT = 22 * mm
_LOGO_TOP_MARGIN = 22 * mm


def _generated_documents_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "generated_documents"


def _resolve_logo_path(db: Session, org_id) -> str | None:
    """Resolve an organization's logo to a readable local file path.

    Remote (http/https) URLs and anything unresolvable yield None so PDF
    generation falls back to the text-only header — a bad logo must never
    break a PDF.
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if org is None or not org.logo_url:
        return None
    url = str(org.logo_url).strip()
    if not url or url.lower().startswith(("http://", "https://")):
        return None

    candidates: list[Path] = []
    candidate = Path(url)
    if candidate.is_absolute():
        candidates.append(candidate)
    else:
        if url.startswith("/documents/"):
            candidates.append(_generated_documents_dir() / unquote(url[len("/documents/") :]))
        candidates.append(Path.cwd() / candidate)
        candidates.append(_generated_documents_dir() / candidate)

    for path in candidates:
        try:
            if path.is_file():
                return str(path)
        except OSError:
            continue
    return None


def _draw_logo(c: "Canvas", logo_path: str, width: float, height: float, margin: float) -> None:
    """Draw the org logo top-right; any failure degrades to the text header."""
    try:
        from reportlab.lib.utils import ImageReader

        reader = ImageReader(logo_path)
        iw, ih = reader.getSize()
        if not iw or not ih or iw < 0 or ih < 0:
            return
        scale = min(_LOGO_MAX_WIDTH / iw, _LOGO_MAX_HEIGHT / ih)
        draw_w, draw_h = iw * scale, ih * scale
        x = width - margin - draw_w
        y = height - _LOGO_TOP_MARGIN - draw_h
        c.drawImage(logo_path, x, y, draw_w, draw_h, mask="auto")
    except Exception:  # noqa: BLE001 - corrupt/unsupported logo: text-only header
        return


def _line_tuples(items) -> list[tuple[str, int, Decimal, Decimal]]:
    return [
        (
            item.description or "-",
            int(item.quantity or 1),
            Decimal(item.unit_price or 0),
            Decimal(item.line_total or 0),
        )
        for item in items
    ]


def recalculate_invoice(db: Session, organization_id, invoice_id: UUID) -> Invoice:
    """Recompute an invoice amount from its line items (subtotal/tax/discount)."""
    invoice = (
        db.query(Invoice)
        .filter(
            Invoice.id == invoice_id,
            Invoice.organization_id == organization_id,
        )
        .first()
    )
    if invoice is None:
        raise ValueError("Invoice not found")

    items = (
        db.query(InvoiceItem)
        .filter(InvoiceItem.invoice_id == invoice_id)
        .all()
    )
    totals = compute_invoice_totals(items)
    invoice.amount = totals["total"]
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def _org_display_name(db: Session, org_id) -> str:
    org = db.query(Organization).filter(Organization.id == org_id).first()
    return org.name if org else ""


def _render_pdf(
    doc_type: str,
    number: str,
    organization_name: str,
    customer_name: str,
    lines,
    total: Decimal,
    logo_path: str | None = None,
) -> io.BytesIO:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 18 * mm

    if logo_path:
        _draw_logo(c, logo_path, width, height, margin)

    c.setFont("Helvetica-Bold", 20)
    c.drawString(margin, height - 26 * mm, f"{organization_name} — {doc_type}")
    c.setFont("Helvetica", 11)
    c.drawString(margin, height - 36 * mm, f"{doc_type} number: {number}")
    c.drawString(margin, height - 44 * mm, f"Customer: {customer_name or '—'}")

    y = height - 66 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y, "Description")
    c.drawString(width - 92 * mm, y, "Qty")
    c.drawString(width - 62 * mm, y, "Unit price")
    c.drawString(width - 22 * mm, y, "Line total")
    y -= 8 * mm

    c.setFont("Helvetica", 10)
    for desc, qty, price, line_total in lines:
        c.drawString(margin, y, str(desc)[:60])
        c.drawString(width - 92 * mm, y, str(qty))
        c.drawString(width - 62 * mm, y, f"{price:.2f}")
        c.drawString(width - 22 * mm, y, f"{line_total:.2f}")
        y -= 8 * mm
        if y < 34 * mm:
            c.showPage()
            y = height - 24 * mm

    c.setFont("Helvetica-Bold", 12)
    c.drawString(width - 70 * mm, y - 12 * mm, f"Total: {total:.2f}")
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


def generate_invoice_pdf(
    db: Session,
    organization_id,
    invoice_id: UUID,
    customer_name: str | None = None,
) -> io.BytesIO:
    invoice = (
        db.query(Invoice)
        .filter(
            Invoice.id == invoice_id,
            Invoice.organization_id == organization_id,
        )
        .first()
    )
    if invoice is None:
        raise ValueError("Invoice not found")
    items = (
        db.query(InvoiceItem)
        .filter(InvoiceItem.invoice_id == invoice_id)
        .all()
    )
    # invoice.amount is the authoritative total (the AI tool stores the sum of
    # the per-line discounted+taxed line_totals). Summing line_total again would
    # double count it.
    customer_name = customer_name or "-"
    return _render_pdf(
        "INVOICE",
        invoice.invoice_number or str(invoice.id),
        _org_display_name(db, organization_id),
        customer_name,
        _line_tuples(items),
        Decimal(invoice.amount or 0),
        logo_path=_resolve_logo_path(db, organization_id),
    )


def generate_quotation_pdf(
    db: Session,
    org_id,
    quotation: Quotation,
    customer_name: str | None = None,
) -> io.BytesIO:
    items = (
        db.query(QuotationItem)
        .filter(QuotationItem.quotation_id == quotation.id)
        .all()
    )
    return _render_pdf(
        "QUOTATION",
        quotation.quotation_number or str(quotation.id),
        _org_display_name(db, org_id),
        customer_name or "-" or "",
        _line_tuples(items),
        Decimal(quotation.total or 0),
        logo_path=_resolve_logo_path(db, org_id),
    )