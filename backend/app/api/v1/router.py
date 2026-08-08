from fastapi import APIRouter

from app.api.v1.organizations.routes import router as organization_router
from app.api.v1.users.routes import router as user_router
from app.api.v1.auth.routes import router as auth_router
from app.api.v1.modules.routes import router as module_router
from app.api.v1.departments.routes import router as department_router

from app.api.v1.ai_chat.routes import router as ai_chat_router
from app.api.v1.ai_conversations.routes import router as ai_conversations_router
from app.api.v1.ai_employees.routes import router as ai_employees_router
from app.api.v1.ai_messages.routes import router as ai_messages_router
from app.api.v1.analytics.routes import router as analytics_router
from app.api.v1.api_keys.routes import router as api_keys_router
from app.api.v1.billing.routes import router as billing_router
from app.api.v1.calendar.routes import router as calendar_router
from app.api.v1.crm.routes import router as crm_router
from app.api.v1.documents.routes import router as documents_router
from app.api.v1.email.routes import router as email_router
from app.api.v1.finance.routes import router as finance_router
from app.api.v1.hr.routes import router as hr_router
from app.api.v1.integrations.routes import router as integrations_router
from app.api.v1.inventory.routes import router as inventory_router
from app.api.v1.knowledge.routes import router as knowledge_router
from app.api.v1.marketing.routes import router as marketing_router
from app.api.v1.organization_settings.routes import router as organization_settings_router
from app.api.v1.sales.routes import router as sales_router
from app.api.v1.storage.routes import router as storage_router
from app.api.v1.tasks.routes import router as tasks_router
from app.api.v1.webhooks.routes import router as webhooks_router
from app.api.v1.whatsapp.routes import router as whatsapp_router
from app.api.v1.workflows.routes import router as workflows_router
from app.api.v1.notifications.routes import router as notifications_router


router = APIRouter()


router.include_router(organization_router)
router.include_router(user_router)
router.include_router(auth_router)
router.include_router(module_router)
router.include_router(department_router)

router.include_router(ai_chat_router)
router.include_router(ai_conversations_router)
router.include_router(ai_employees_router)
router.include_router(ai_messages_router)
router.include_router(analytics_router)
router.include_router(api_keys_router)
router.include_router(billing_router)
router.include_router(calendar_router)
router.include_router(crm_router)
router.include_router(documents_router)
router.include_router(email_router)
router.include_router(finance_router)
router.include_router(hr_router)
router.include_router(integrations_router)
router.include_router(inventory_router)
router.include_router(knowledge_router)
router.include_router(marketing_router)
router.include_router(organization_settings_router)
router.include_router(sales_router)
router.include_router(storage_router)
router.include_router(tasks_router)
router.include_router(webhooks_router)
router.include_router(whatsapp_router)
router.include_router(workflows_router)
router.include_router(notifications_router)
