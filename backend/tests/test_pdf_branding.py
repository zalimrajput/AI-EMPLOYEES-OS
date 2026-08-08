"""PDF branding tests: org logo drawn when resolvable, graceful otherwise."""
import io
import sys
import uuid
from decimal import Decimal

sys.path.insert(0, ".")

import pytest

from sqlalchemy import text


def _teardown(db, org):
    deletes = [
        "DELETE FROM invoice_items WHERE organization_id = :id",
        "DELETE FROM invoices WHERE organization_id = :id",
        "DELETE FROM quotation_items WHERE organization_id = :id",
        "DELETE FROM quotations WHERE organization_id = :id",
        "DELETE FROM customers WHERE organization_id = :id",
        "DELETE FROM organizations WHERE id = :id",
    ]
    for statement in deletes:
        db.execute(text(statement), {"id": org.id})
    db.commit()


def _org(db, logo_url=None):
    from app.models.organization import Organization

    org = Organization(
        name="Branded Org",
        slug=f"brand-{uuid.uuid4().hex[:10]}",
        settings={},
        logo_url=logo_url,
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def _invoice(db, org):
    from app.models.invoice import Invoice, InvoiceItem

    inv = Invoice(
        organization_id=org.id,
        invoice_number=f"INV-{uuid.uuid4().hex[:6].upper()}",
        amount=Decimal("88.00"),
        status="unpaid",
    )
    db.add(inv)
    db.flush()
    db.add(
        InvoiceItem(
            organization_id=org.id,
            invoice_id=inv.id,
            description="Widget",
            quantity=1,
            unit_price=Decimal("88.00"),
            tax_rate=Decimal("0"),
            discount=Decimal("0"),
            line_total=Decimal("88.00"),
            sort_order=0,
        )
    )
    db.commit()
    db.refresh(inv)
    return inv


def _png_bytes(size=64):
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (size, size), (200, 40, 40)).save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.db
def test_pdf_renders_with_working_logo(db, tmp_path):
    from app.services.invoice_service import generate_invoice_pdf

    logo_file = tmp_path / "logo.png"
    logo_file.write_bytes(_png_bytes())
    org = _org(db, logo_url=str(logo_file))
    inv = _invoice(db, org)

    try:
        data = generate_invoice_pdf(db, org.id, inv.id, customer_name="Cust").getvalue()
        assert isinstance(data, bytes)
        assert data.startswith(b"%PDF")
        assert len(data) > 1000  # logo image embedded makes it substantially larger
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_pdf_renders_with_broken_logo_url_without_raising(db):
    from app.services.invoice_service import generate_invoice_pdf

    org = _org(db, logo_url="https://unreachable.invalid/assets/logo.png")
    inv = _invoice(db, org)

    try:
        data = generate_invoice_pdf(db, org.id, inv.id, customer_name="Cust").getvalue()
        assert isinstance(data, bytes)
        assert data.startswith(b"%PDF")
        assert len(data) > 0
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_pdf_renders_with_missing_local_logo_without_raising(db, tmp_path):
    from app.services.invoice_service import generate_invoice_pdf

    org = _org(db, logo_url=str(tmp_path / "does-not-exist.png"))
    inv = _invoice(db, org)

    try:
        data = generate_invoice_pdf(db, org.id, inv.id).getvalue()
        assert isinstance(data, bytes)
        assert data.startswith(b"%PDF")
        assert len(data) > 0
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_quotation_pdf_renders_with_logo(db, tmp_path):
    from app.models.quotation import Quotation, QuotationItem
    from app.services.invoice_service import generate_quotation_pdf

    logo_file = tmp_path / "logo.png"
    logo_file.write_bytes(_png_bytes())
    org = _org(db, logo_url=str(logo_file))

    quotation = Quotation(
        organization_id=org.id,
        quotation_number="QUO-LOGO",
        status="approved",
        subtotal=Decimal("50.00"),
        tax=Decimal("0"),
        discount=Decimal("0"),
        total=Decimal("50.00"),
    )
    db.add(quotation)
    db.flush()
    db.add(
        QuotationItem(
            organization_id=org.id,
            quotation_id=quotation.id,
            description="Item",
            quantity=1,
            unit_price=Decimal("50.00"),
            line_total=Decimal("50.00"),
            sort_order=0,
        )
    )
    db.commit()

    try:
        data = generate_quotation_pdf(db, org.id, quotation, "Cust").getvalue()
        assert isinstance(data, bytes)
        assert data.startswith(b"%PDF")
        assert len(data) > 1000
    finally:
        _teardown(db, org)