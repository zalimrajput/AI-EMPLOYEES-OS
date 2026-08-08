# DATABASE_MAPPING.md

This document maps the core database tables to their corresponding Python backend implementation layers and the frontend views that consume them.

## Identity & Access

### Table: `users`
- **SQLAlchemy Model:** `models/user.py`
- **Pydantic Schema:** `schemas/user.py`
- **Router:** `api/v1/users/routes.py`
- **Service:** `services/user_service.py`
- **Frontend Pages:** `/dashboard/settings`, `/login`, `/dashboard/employee`
- **Status:** Partially Implemented (Model drifts from schema).

### Table: `organizations`
- **SQLAlchemy Model:** `models/organization.py`
- **Pydantic Schema:** `schemas/organization.py`
- **Router:** `api/v1/organizations/routes.py`
- **Service:** `services/organization_service.py`
- **Frontend Pages:** `/register`, `/dashboard/settings`
- **Status:** Partially Implemented.

## AI Engine

### Table: `ai_employees`
- **SQLAlchemy Model:** `models/ai_employee.py`
- **Pydantic Schema:** `schemas/ai_employee.py`
- **Router:** `api/v1/ai_employees/routes.py`
- **Service:** Missing.
- **Frontend Pages:** `/dashboard/employees`
- **Status:** Missing (Stub files only).

### Table: `ai_conversations`
- **SQLAlchemy Model:** `models/ai_conversation.py`
- **Pydantic Schema:** `schemas/ai_conversation.py`
- **Router:** `api/v1/ai_conversations/routes.py`
- **Service:** `services/ai_conversation_service.py`
- **Frontend Pages:** `/dashboard/chat`
- **Status:** Missing (Stub files only).

### Table: `ai_messages`
- **SQLAlchemy Model:** `models/ai_message.py`
- **Pydantic Schema:** `schemas/ai_message.py`
- **Router:** `api/v1/ai_messages/routes.py`
- **Service:** `services/ai_message_service.py`
- **Frontend Pages:** `/dashboard/chat`
- **Status:** Missing (Stub files only).

## CRM

### Table: `customers`
- **SQLAlchemy Model:** `models/customer.py`
- **Pydantic Schema:** `schemas/crm.py`
- **Router:** `api/v1/crm/routes.py`
- **Service:** `services/crm_service.py`
- **Frontend Pages:** `/dashboard/crm`
- **Status:** Missing.

### Table: `leads`
- **SQLAlchemy Model:** `models/lead.py`
- **Pydantic Schema:** `schemas/crm.py`
- **Router:** `api/v1/crm/routes.py`
- **Service:** `services/crm_service.py`
- **Frontend Pages:** `/dashboard/crm`
- **Status:** Missing.

## Invoicing

### Table: `invoices`
- **SQLAlchemy Model:** `models/invoice.py`
- **Pydantic Schema:** `schemas/invoice.py`
- **Router:** `api/v1/finance/routes.py`
- **Service:** `services/invoice_service.py`
- **Frontend Pages:** `/dashboard/finance`
- **Status:** Missing.
