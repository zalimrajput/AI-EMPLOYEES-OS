"""Organization settings: get-or-create + update, thin layer over the model."""
from sqlalchemy.orm import Session

from app.models.organization_settings import OrganizationSettings


def get_settings(db: Session, organization_id) -> OrganizationSettings:
    row = (
        db.query(OrganizationSettings)
        .filter(OrganizationSettings.organization_id == organization_id)
        .first()
    )
    if row is None:
        row = OrganizationSettings(organization_id=organization_id)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def update_settings(
    db: Session, organization_id, updates: dict
) -> OrganizationSettings:
    allowed = {
        "company_name",
        "timezone",
        "language",
        "currency",
        "tax_rate",
        "invoice_prefix",
        "quotation_prefix",
        "date_format",
        "logo_url",
    }
    row = get_settings(db, organization_id)
    for key, value in updates.items():
        if key in allowed and value is not None:
            setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row