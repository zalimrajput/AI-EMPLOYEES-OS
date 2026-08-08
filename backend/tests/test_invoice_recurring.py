"""Recurring invoice + tax/discount calculation tests (live Postgres).

Covers:
- create_invoice with line items: exact tax/discount math (tax on discounted
  price) and real InvoiceItem rows.
- Backward-compatible flat-amount path.
- create_quotation applying the same per-line formula.
- create_invoice recurrence: next_billing_date computed.
- recurring_invoice_worker.generate_due_recurring_invoices: due generates
  exactly one copy, not-due generates nothing, second run same day is
  idempotent.
"""
import sys
import uuid
from datetime import date, timedelta

sys.path.insert(0, ".")

from decimal import Decimal

import pytest

from sqlalchemy import text

from app.ai.tools.invoice_tools import INVOICE_TOOLS


def _teardown(db, org):
    deletes = [
        "DELETE FROM storage_files WHERE organization_id = :id",
        "DELETE FROM storage_quotas WHERE organization_id = :id",
        "DELETE FROM quotation_items WHERE organization_id = :id",
        "DELETE FROM invoice_items WHERE organization_id = :id",
        "DELETE FROM invoices WHERE organization_id = :id",
        "DELETE FROM quotations WHERE organization_id = :id",
        "DELETE FROM reminders WHERE organization_id = :id",
        "DELETE FROM activities WHERE organization_id = :id",
        "DELETE FROM notifications WHERE organization_id = :id",
        "DELETE FROM customers WHERE organization_id = :id",
        "DELETE FROM users WHERE organization_id = :id",
        "DELETE FROM ai_employees WHERE organization_id = :id",
        "DELETE FROM organizations WHERE id = :id",
    ]
    for statement in deletes:
        db.execute(text(statement), {"id": org.id})
    db.commit()


def _org(db):
    from app.models.organization import Organization

    org = Organization(
        name="Recurring Org",
        slug=f"rec-{uuid.uuid4().hex[:10]}",
        settings={},
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def _customer(db, org):
    from app.models.customer import Customer

    cust = Customer(organization_id=org.id, name="Recurring Customer")
    db.add(cust)
    db.commit()
    db.refresh(cust)
    return cust


@pytest.mark.db
def test_create_invoice_items_tax_on_discounted_price(db):
    """amount == sum(line (qty*price*(1-disc/100))*(1+tax/100))."""
    from app.models.invoice import Invoice, InvoiceItem

    org = _org(db)
    cust = _customer(db, org)
    try:
        res = INVOICE_TOOLS["create_invoice"].handler(
            db,
            org.id,
            None,
            {
                "customer_id": str(cust.id),
                "invoice_number": "INV-TAX-1",
                "items": [
                    {"description": "Widget", "quantity": 2, "unit_price": 100.00, "tax_rate": 10, "discount": 20},
                    {"description": "Service", "quantity": 1, "unit_price": 50.00, "tax_rate": 5, "discount": 0},
                ],
            },
        )
        assert res.get("id")
        assert res["items"] == 2
        # line 1: (2*100*(1-0.20))*(1+0.10) = 160*1.10 = 176.00
        # line 2: (1*50*(1-0.00))*(1+0.05) = 50*1.05 = 52.50
        # total: 176.00 + 52.50 = 228.50
        assert Decimal(str(res["amount"])) == Decimal("228.50")

        fresh = db.query(Invoice).filter(Invoice.id == _uuid_of(res["id"])).first()
        assert Decimal(str(fresh.amount)) == Decimal("228.50")

        rows = (
            db.query(InvoiceItem)
            .filter(InvoiceItem.invoice_id == fresh.id)
            .order_by(InvoiceItem.sort_order)
            .all()
        )
        assert len(rows) == 2
        assert Decimal(str(rows[0].line_total)) == Decimal("176.00")
        assert Decimal(str(rows[0].tax_rate)) == Decimal("10")
        assert Decimal(str(rows[0].discount)) == Decimal("20")
        assert Decimal(str(rows[1].line_total)) == Decimal("52.50")
        assert Decimal(str(rows[1].tax_rate)) == Decimal("5")
        assert Decimal(str(rows[1].discount)) == Decimal("0")
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_create_invoice_flat_amount_backward_compatible(db):
    """No items -> amount set verbatim, no InvoiceItem rows, status unpaid."""
    from app.models.invoice import Invoice, InvoiceItem

    org = _org(db)
    cust = _customer(db, org)
    try:
        res = INVOICE_TOOLS["create_invoice"].handler(
            db,
            org.id,
            None,
            {
                "customer_id": str(cust.id),
                "invoice_number": "INV-FLAT-1",
                "amount": 99.99,
            },
        )
        assert res["items"] == 0
        assert Decimal(str(res["amount"])) == Decimal("99.99")

        fresh = db.query(Invoice).filter(Invoice.id == _uuid_of(res["id"])).first()
        assert Decimal(str(fresh.amount)) == Decimal("99.99")
        assert fresh.status == "unpaid"
        rows = (
            db.query(InvoiceItem).filter(InvoiceItem.invoice_id == fresh.id).count()
        )
        assert rows == 0
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_create_quotation_applies_tax_and_discount_per_line(db):
    """Quotation totals use the same per-line formula as invoices."""
    from app.models.quotation import Quotation, QuotationItem

    org = _org(db)
    cust = _customer(db, org)
    try:
        res = INVOICE_TOOLS["create_quotation"].handler(
            db,
            org.id,
            None,
            {
                "customer_id": str(cust.id),
                "quotation_number": "QT-1",
                "items": [
                    {"description": "Item A", "quantity": 2, "unit_price": 100.00, "tax_rate": 10, "discount": 20},
                    {"description": "Item B", "quantity": 1, "unit_price": 40.00},
                ],
                "tax_rate": 7,
                "discount": 10,
            },
        )
        # item A: (2*100*(1-0.20))*(1+0.10) = 176.00 (line overrides doc)
        # item B: (1*40*(1-0.10))*(1+0.07) = 36*1.07 = 38.52 (doc defaults)
        # total: 176.00 + 38.52 = 214.52
        assert Decimal(res["total"]) == Decimal("214.52")

        q = db.query(Quotation).filter(Quotation.id == _uuid_of(res["id"])).first()
        rows = (
            db.query(QuotationItem)
            .filter(QuotationItem.quotation_id == q.id)
            .order_by(QuotationItem.sort_order)
            .all()
        )
        assert len(rows) == 2
        assert Decimal(str(rows[0].line_total)) == Decimal("176.00")
        assert Decimal(str(rows[1].line_total)) == Decimal("38.52")
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_create_invoice_recurrence_sets_next_billing_date(db):
    """monthly interval advances next_billing_date relative to due_date."""
    from app.models.invoice import Invoice

    org = _org(db)
    cust = _customer(db, org)
    try:
        due = date.today() + timedelta(days=3)
        res = INVOICE_TOOLS["create_invoice"].handler(
            db,
            org.id,
            None,
            {
                "customer_id": str(cust.id),
                "invoice_number": "INV-REC-1",
                "amount": 120.00,
                "due_date": due.isoformat(),
                "recurrence_interval": 1,
                "recurrence_period": "monthly",
            },
        )
        fresh = db.query(Invoice).filter(Invoice.id == _uuid_of(res["id"])).first()
        assert fresh.recurrence_period == "monthly"
        assert fresh.recurrence_interval == 1
        assert fresh.next_billing_date is not None
        assert fresh.next_billing_date >= due
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_recurring_worker_due_invoice_generates_one_copy(db):
    """A due recurring invoice produces exactly one new invoice with copied
    line items and an advanced next_billing_date."""
    from app.models.invoice import Invoice, InvoiceItem
    from workers.recurring_invoice_worker import generate_due_recurring_invoices

    org = _org(db)
    cust = _customer(db, org)

    source = Invoice(
        organization_id=org.id,
        customer_id=cust.id,
        invoice_number="INV-REC-2",
        amount=Decimal("228.50"),
        status="unpaid",
        due_date=date.today() - timedelta(days=1),
        recurrence_interval=1,
        recurrence_period="monthly",
        next_billing_date=date.today() - timedelta(days=1),
    )
    db.add(source)
    db.flush()
    db.add(
        InvoiceItem(
            organization_id=org.id,
            invoice_id=source.id,
            description="Widget",
            quantity=2,
            unit_price=Decimal("100.00"),
            tax_rate=Decimal("10"),
            discount=Decimal("20"),
            line_total=Decimal("176.00"),
        )
    )
    db.commit()
    db.refresh(source)

    try:
        result = generate_due_recurring_invoices(organization_id=org.id)
        assert result["generated"] == 1
        assert result["skipped"] == 0

        copies = (
            db.query(Invoice)
            .filter(
                Invoice.organization_id == org.id,
                Invoice.id != source.id,
            )
            .all()
        )
        assert len(copies) == 1
        copy = copies[0]
        assert copy.customer_id == cust.id
        assert Decimal(str(copy.amount)) == Decimal("228.50")
        assert copy.status == "unpaid"
        # due_date of the copy is the source's (old) billing date
        assert copy.due_date == source.due_date

        copied_items = (
            db.query(InvoiceItem).filter(InvoiceItem.invoice_id == copy.id).all()
        )
        assert len(copied_items) == 1
        assert Decimal(str(copied_items[0].line_total)) == Decimal("176.00")
        assert Decimal(str(copied_items[0].tax_rate)) == Decimal("10")

        # source advanced ~1 month into the future
        db.refresh(source)
        assert source.next_billing_date is not None
        assert source.next_billing_date > date.today()
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_recurring_worker_not_due_generates_nothing(db):
    from app.models.invoice import Invoice
    from workers.recurring_invoice_worker import generate_due_recurring_invoices

    org = _org(db)
    cust = _customer(db, org)

    future = Invoice(
        organization_id=org.id,
        customer_id=cust.id,
        invoice_number="INV-REC-3",
        amount=Decimal("50.00"),
        status="unpaid",
        recurrence_interval=1,
        recurrence_period="weekly",
        next_billing_date=date.today() + timedelta(days=7),
    )
    db.add(future)
    db.commit()
    db.refresh(future)

    try:
        result = generate_due_recurring_invoices(organization_id=org.id)
        assert result["generated"] == 0
        total = (
            db.query(Invoice).filter(Invoice.organization_id == org.id).count()
        )
        assert total == 1  # only the source, nothing new
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_recurring_worker_idempotent_same_day(db):
    """Running twice the same day does not double-generate."""
    from app.models.invoice import Invoice
    from workers.recurring_invoice_worker import generate_due_recurring_invoices

    org = _org(db)
    cust = _customer(db, org)

    source = Invoice(
        organization_id=org.id,
        customer_id=cust.id,
        invoice_number="INV-REC-4",
        amount=Decimal("60.00"),
        status="unpaid",
        recurrence_interval=1,
        recurrence_period="monthly",
        next_billing_date=date.today() - timedelta(days=1),
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    try:
        first = generate_due_recurring_invoices(organization_id=org.id)
        assert first["generated"] == 1
        second = generate_due_recurring_invoices(organization_id=org.id)
        assert second["generated"] == 0

        copies = (
            db.query(Invoice)
            .filter(
                Invoice.organization_id == org.id,
                Invoice.id != source.id,
            )
            .count()
        )
        assert copies == 1
    finally:
        _teardown(db, org)


def _uuid_of(text_id):
    from uuid import UUID

    return UUID(str(text_id))

@pytest.mark.db
def test_compute_invoice_totals_matches_tool_convention(db):
    """compute_invoice_totals / recalculate_invoice agree with create_invoice.

    This test would have caught the formula divergence: the tool stores
    tax-on-discounted-price per line; before reconciliation compute_invoice_totals
    used tax-on-full-price and reported a different total.
    """
    from app.models.invoice import Invoice, InvoiceItem
    from app.repositories.invoice_repository import compute_invoice_totals
    from app.services.invoice_service import recalculate_invoice

    org = _org(db)
    cust = _customer(db, org)
    try:
        res = INVOICE_TOOLS["create_invoice"].handler(
            db,
            org.id,
            None,
            {
                "customer_id": str(cust.id),
                "invoice_number": "INV-CONSIST-1",
                "items": [
                    {"description": "Widget", "quantity": 2, "unit_price": 100.00, "tax_rate": 10, "discount": 20},
                    {"description": "Service", "quantity": 1, "unit_price": 50.00, "tax_rate": 5, "discount": 0},
                ],
            },
        )
        stored = Decimal(str(res["amount"]))  # 228.50 per the tool formula

        fresh = db.query(Invoice).filter(Invoice.id == _uuid_of(res["id"])).first()
        rows = (
            db.query(InvoiceItem)
            .filter(InvoiceItem.invoice_id == fresh.id)
            .all()
        )
        totals = compute_invoice_totals(rows)
        # recomputed total equals exactly what the tool stored
        assert totals["total"] == stored
        # subtotal is the sum of gross line values
        assert totals["subtotal"] == Decimal("250.00")

        # recalculate_invoice writes the SAME amount back (no drift)
        recalc = recalculate_invoice(db, org.id, fresh.id)
        assert Decimal(str(recalc.amount)) == stored
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_generate_invoice_pdf_total_equals_stored(db):
    """generate_invoice_pdf must not double-count line totals.

    The real live bug: PDF summed line_total AND invoice.amount, showing 2x.
    The rendered total should equal the tool-stored amount.
    """
    import io

    from app.models.invoice import Invoice, InvoiceItem
    from app.services.invoice_service import generate_invoice_pdf

    org = _org(db)
    cust = _customer(db, org)
    try:
        res = INVOICE_TOOLS["create_invoice"].handler(
            db,
            org.id,
            None,
            {
                "customer_id": str(cust.id),
                "invoice_number": "INV-PDF-1",
                "items": [
                    {"description": "Widget", "quantity": 2, "unit_price": 100.00, "tax_rate": 10, "discount": 20},
                ],
            },
        )
        stored = Decimal(str(res["amount"]))  # 176.00
        fresh = db.query(Invoice).filter(Invoice.id == _uuid_of(res["id"])).first()

        buffer = generate_invoice_pdf(db, org.id, fresh.id, customer_name="Cust")
        data = buffer.getvalue()
        assert isinstance(data, bytes)
        assert len(data) > 0  # a real PDF was produced

        # The rendered total text must reflect the stored amount (not 2x it).
        # Extract the "Total:" line from the PDF text.
        from pypdf import PdfReader
        import io as _io

        reader = PdfReader(_io.BytesIO(data))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
        assert f"Total: {stored:.2f}" in text, f"PDF total mismatch. PDF text:\n{text}"
    finally:
        _teardown(db, org)
