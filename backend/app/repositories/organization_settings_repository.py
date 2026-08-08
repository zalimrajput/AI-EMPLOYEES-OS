from sqlalchemy.orm import Session

from app.models.organization_settings import OrganizationSettings


class OrganizationSettingsRepository:
    model = OrganizationSettings

    def __init__(self, db: Session, organization_id) -> None:
        self.db = db
        self.organization_id = organization_id

    def get_or_create(self) -> OrganizationSettings:
        row = (
            self.db.query(OrganizationSettings)
            .filter(OrganizationSettings.organization_id == self.organization_id)
            .first()
        )
        if row is None:
            row = OrganizationSettings(organization_id=self.organization_id)
            self.db.add(row)
            self.db.commit()
            self.db.refresh(row)
        return row