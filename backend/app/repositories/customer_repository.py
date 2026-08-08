from uuid import UUID

from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.lead import Lead
from app.repositories.base import BaseRepository


class CustomerRepository(BaseRepository):
    model = Customer


class LeadRepository(BaseRepository):
    model = Lead

    def convert(self, lead: Lead, customer_name: str) -> Customer:
        customer = Customer(
            organization_id=self.organization_id,
            name=customer_name or lead.name or "Unnamed customer",
            email=lead.email,
            phone=lead.phone,
            company=lead.company,
            status="active",
        )
        self.db.add(customer)
        self.db.flush()
        lead.converted_customer_id = customer.id
        lead.status = "converted"
        self.db.commit()
        self.db.refresh(customer)
        return customer