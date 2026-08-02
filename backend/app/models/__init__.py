from app.models.base import Base

from app.models.organization import Organization
from app.models.user import User
from app.models.role import Role
from app.models.user_role import UserRole
from app.models.department import Department
from app.models.organization_settings import OrganizationSettings
from app.models.integration import Integration
from app.models.platform import PlatformRole, PlatformSetting, PlatformLog

from app.models.ai_employee import AIEmployee
from app.models.ai_conversation import AIConversation
from app.models.ai_message import AIMessage
from app.models.ai_memory import AIMemory

from app.models.customer import Customer
from app.models.lead import Lead
from app.models.pipeline import Pipeline, Deal
from app.models.product import Product
from app.models.quotation import Quotation, QuotationItem
from app.models.invoice import Invoice, InvoiceItem
from app.models.payment import Payment
from app.models.activity import Activity
from app.models.reminder import Reminder

from app.models.email import EmailThread, Email
from app.models.whatsapp import WhatsAppContact, WhatsAppMessage
from app.models.task import Task
from app.models.meeting import Meeting
from app.models.document import Document
from app.models.knowledge_base import KnowledgeArticle
from app.models.workflow import Workflow
from app.models.notification import Notification
from app.models.audit_log import AuditLog

from app.models.storage import StorageFile, StorageQuota, FileAccessPermission
from app.models.subscription import Plan, Subscription, BillingTransaction
from app.models.usage import UsageRecord, StorageUsage, APIUsage
from app.models.api_key import APIKey, Webhook, APIRequest
from app.models.report import Dashboard, DashboardRoleAccess, Report, AnalyticsEvent, BusinessMetric
from app.models.security import UserSession, MFASetting, SSOConnection, SecurityEvent

from app.models.hr import Employee, Attendance, LeaveRequest, JobCandidate
from app.models.finance import ExpenseCategory, Expense, Budget, FinancialReport
from app.models.inventory import (
    Warehouse,
    Supplier,
    InventoryItem,
    StockMovement,
    PurchaseOrder,
)
from app.models.marketing import (
    MarketingCampaign,
    AudienceSegment,
    MarketingContent,
    EmailCampaign,
)


__all__ = [
    "Base",

    "Organization",
    "User",
    "Role",
    "UserRole",
    "Department",
    "OrganizationSettings",
    "Integration",
    "PlatformRole",
    "PlatformSetting",
    "PlatformLog",

    "AIEmployee",
    "AIConversation",
    "AIMessage",
    "AIMemory",

    "Customer",
    "Lead",
    "Pipeline",
    "Deal",
    "Product",
    "Quotation",
    "QuotationItem",
    "Invoice",
    "InvoiceItem",
    "Payment",
    "Activity",
    "Reminder",

    "EmailThread",
    "Email",
    "WhatsAppContact",
    "WhatsAppMessage",
    "Task",
    "Meeting",
    "Document",
    "KnowledgeArticle",
    "Workflow",
    "Notification",
    "AuditLog",

    "StorageFile",
    "StorageQuota",
    "FileAccessPermission",
    "Plan",
    "Subscription",
    "BillingTransaction",
    "UsageRecord",
    "StorageUsage",
    "APIUsage",
    "APIKey",
    "Webhook",
    "APIRequest",
    "Dashboard",
    "DashboardRoleAccess",
    "Report",
    "AnalyticsEvent",
    "BusinessMetric",
    "UserSession",
    "MFASetting",
    "SSOConnection",
    "SecurityEvent",

    "Employee",
    "Attendance",
    "LeaveRequest",
    "JobCandidate",
    "ExpenseCategory",
    "Expense",
    "Budget",
    "FinancialReport",
    "Warehouse",
    "Supplier",
    "InventoryItem",
    "StockMovement",
    "PurchaseOrder",
    "MarketingCampaign",
    "AudienceSegment",
    "MarketingContent",
    "EmailCampaign",
]
