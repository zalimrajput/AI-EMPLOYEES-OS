from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1._crud import require_org_member
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.ai_conversation import AIConversation
from app.models.ai_employee import AIEmployee
from app.models.customer import Customer
from app.models.document import Document
from app.models.email import Email
from app.models.finance import Expense
from app.models.hr import Employee
from app.models.invoice import Invoice
from app.models.inventory import InventoryItem
from app.models.lead import Lead
from app.models.marketing import MarketingCampaign
from app.models.meeting import Meeting
from app.models.notification import Notification
from app.models.payment import Payment
from app.models.quotation import Quotation
from app.models.task import Task
from app.models.whatsapp import WhatsAppMessage
from app.models.workflow import Workflow


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


def _count(db: Session, model, organization_id) -> int:
    return (
        db.query(model)
        .filter(model.organization_id == organization_id)
        .count()
    )


@router.get("/summary")
# Protected endpoint: aggregate live counts for the caller's organization.
def analytics_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    me = require_org_member(db, current_user)
    org_id = me.organization_id
    return {
        "customers": _count(db, Customer, org_id),
        "leads": _count(db, Lead, org_id),
        "quotations": _count(db, Quotation, org_id),
        "invoices": _count(db, Invoice, org_id),
        "payments": _count(db, Payment, org_id),
        "tasks": _count(db, Task, org_id),
        "meetings": _count(db, Meeting, org_id),
        "documents": _count(db, Document, org_id),
        "emails": _count(db, Email, org_id),
        "whatsapp_messages": _count(db, WhatsAppMessage, org_id),
        "workflows": _count(db, Workflow, org_id),
        "ai_employees": _count(db, AIEmployee, org_id),
        "ai_conversations": _count(db, AIConversation, org_id),
        "employees": _count(db, Employee, org_id),
        "expenses": _count(db, Expense, org_id),
        "inventory_items": _count(db, InventoryItem, org_id),
        "campaigns": _count(db, MarketingCampaign, org_id),
        "notifications": _count(db, Notification, org_id),
    }
