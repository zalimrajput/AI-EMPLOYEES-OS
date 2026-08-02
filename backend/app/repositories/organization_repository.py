from sqlalchemy.orm import Session

from app.models.organization import Organization


class OrganizationRepository:


    def create(
        self,
        db:Session,
        organization:Organization
    ):

        db.add(organization)

        db.commit()

        db.refresh(
            organization
        )

        return organization