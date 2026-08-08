from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.invoice import Invoice, InvoiceItem

_ROUND = Decimal("0.01")


def compute_invoice_totals(items: list[InvoiceItem]) -> dict:
    """Sum line totals into subtotal, tax, discount and final total.

    Convention (matches the AI tool ``_compute_item_totals``): tax is applied
    on the DISCOUNTED price, and ``discount`` is a percentage per line:
        gross = quantity * unit_price
        discounted = gross * (1 - discount / 100)
        line_total = discounted * (1 + tax_rate / 100)
    Each line is rounded to 2 decimals (ROUND_HALF_UP), then summed into the
    total (also rounded).
    """
    from decimal import ROUND_HALF_UP

    subtotal = Decimal("0.00")
    tax = Decimal("0.00")
    discount_amount = Decimal("0.00")
    total = Decimal("0.00")
    for item in items:
        quantity = Decimal(item.quantity or 0)
        unit_price = Decimal(item.unit_price or 0)
        tax_rate = Decimal(item.tax_rate or 0)
        discount = Decimal(item.discount or 0)

        gross = quantity * unit_price
        discounted = gross * (Decimal("1") - discount / Decimal("100"))
        line_total = (discounted * (Decimal("1") + tax_rate / Decimal("100"))).quantize(
            _ROUND, rounding=ROUND_HALF_UP
        )

        subtotal += gross
        tax += discounted * tax_rate / Decimal("100")
        discount_amount += gross * discount / Decimal("100")
        total += line_total

    return {
        "subtotal": subtotal.quantize(_ROUND),
        "tax": tax.quantize(_ROUND),
        "discount": discount_amount.quantize(_ROUND),
        "total": total.quantize(_ROUND),
    }


class InvoiceRepository:
    def __init__(self, db: Session, organization_id) -> None:
        self.db = db
        self.organization_id = organization_id

    def get(self, invoice_id, raise_missing: bool = True) -> Invoice | None:
        row = (
            self.db.query(Invoice)
            .filter(
                Invoice.id == invoice_id,
                Invoice.organization_id == self.organization_id,
            )
            .first()
        )
        if row is None and raise_missing:
            raise ValueError("Invoice not found")
        return row

    def list_for_customer(self, customer_id) -> list[Invoice]:
        return (
            self.db.query(Invoice)
            .filter(
                Invoice.organization_id == self.organization_id,
                Invoice.customer_id == customer_id,
            )
            .order_by(Invoice.created_at.desc())
            .all()
        )