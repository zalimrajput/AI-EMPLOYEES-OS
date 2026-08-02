"""Robust audit of every core business table on the live DB.

Rolls back after each failure so a single missing table doesn't abort the
rest of the audit (psycopg2 aborts the whole transaction on error).
"""
import os
from sqlalchemy import create_engine, text

url = os.environ.get("DATABASE_URL")
e = create_engine(url)

tables = [
    # Multi-tenant core
    "organizations", "users", "roles", "user_roles", "departments",
    "organization_settings", "platform_roles", "subscriptions", "plans", "usage",
    # CRM / Sales
    "customers", "leads", "pipelines", "products",
    "quotations", "quotation_items", "invoices", "invoice_items", "payments",
    # Productivity
    "tasks", "meetings", "reminders", "workflows",
    # Communication
    "emails", "whatsapp",
    # AI
    "ai_employees", "ai_memories", "ai_conversations", "ai_messages",
    # Documents / knowledge
    "documents", "knowledge_base",
    # Platform
    "reports", "notifications", "audit_logs", "api_keys", "integrations",
    "modules", "org_modules", "widgets", "dashboards", "dashboard_role_access",
    # Security / storage
    "storage_files",
]

with e.connect() as c:
    for t in tables:
        try:
            n = c.execute(text(f'SELECT COUNT(*) FROM {t}')).scalar()
            print(f"  {t}: {n}")
        except Exception:
            # Roll back so the next query isn't poisoned by the aborted txn.
            c.rollback()
            # Distinguish "table missing" from other errors.
            exists = c.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name = :t"
                ),
                {"t": t},
            ).scalar()
            c.rollback()
            if exists:
                print(f"  {t}: EXISTS (row count failed)")
            else:
                print(f"  {t}: MISSING")
