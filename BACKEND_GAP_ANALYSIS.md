# BACKEND_GAP_ANALYSIS.md

This document maps the existing frontend pages to the backend REST API endpoints they require to function, identifying the gap between the UI's needs and the backend's current implementation state.

### `dashboard/crm`
**Needs:**
- `GET /api/v1/crm/customers`
- `GET /api/v1/crm/leads`
- `GET /api/v1/crm/activities`
- `GET /api/v1/crm/stats`
**Missing:** Everything. The `crm` router is an empty stub.
**Priority:** High

### `dashboard/chat`
**Needs:**
- `GET /api/v1/ai-chat/conversations`
- `POST /api/v1/ai-chat/conversations`
- `GET /api/v1/ai-chat/conversations/{id}/messages`
- `POST /api/v1/ai-chat/messages` (Streaming)
**Missing:** Everything. All AI engine and router files are 0-byte stubs.
**Priority:** Critical

### `dashboard/employees` (AI Agents List)
**Needs:**
- `GET /api/v1/ai-employees`
- `GET /api/v1/ai-employees/{id}`
**Missing:** Everything.
**Priority:** High

### `dashboard/tasks`
**Needs:**
- `GET /api/v1/tasks`
- `POST /api/v1/tasks`
- `PATCH /api/v1/tasks/{id}`
**Missing:** Everything.
**Priority:** Medium

### `dashboard/finance`
**Needs:**
- `GET /api/v1/finance/invoices`
- `GET /api/v1/finance/expenses`
- `GET /api/v1/finance/stats`
**Missing:** Everything.
**Priority:** Medium

### `dashboard/hr`
**Needs:**
- `GET /api/v1/hr/employees` (Human employees)
- `GET /api/v1/hr/leave-requests`
**Missing:** Everything.
**Priority:** Low

### `dashboard/marketing`
**Needs:**
- `GET /api/v1/marketing/campaigns`
- `GET /api/v1/marketing/segments`
**Missing:** Everything.
**Priority:** Low

### `dashboard/sales`
**Needs:**
- `GET /api/v1/sales/pipelines`
- `GET /api/v1/sales/deals`
- `GET /api/v1/sales/quotations`
**Missing:** Everything.
**Priority:** Medium

### `dashboard/analytics`
**Needs:**
- `GET /api/v1/analytics/summary`
**Missing:** Everything.
**Priority:** Low

### `dashboard/billing`
**Needs:**
- `GET /api/v1/billing/subscriptions`
- `GET /api/v1/billing/invoices`
- `GET /api/v1/billing/plans`
**Missing:** Everything.
**Priority:** Low

### `dashboard/settings`
**Needs:**
- `GET /api/v1/organization-settings`
- `PATCH /api/v1/organization-settings`
- `GET /api/v1/users` (List org members)
- `POST /api/v1/users` (Invite user)
**Missing:** `organization-settings` is an empty stub. `users` exists partially but relies on broken auth logic.
**Priority:** High

### `dashboard/super-admin`
**Needs:**
- `GET /api/v1/organizations` (List all orgs)
- `GET /api/v1/modules` (Manage enabled modules globally)
- `GET /api/v1/platform-logs`
**Missing:** `organizations` exists but needs updating. Others are missing.
**Priority:** Medium

### `/login` & `/register`
**Needs:**
- `GET /api/v1/auth/me` (Verify session and fetch profile/org data)
- `POST /api/v1/organizations` (Create new workspace on register)
**Missing:** `auth/me` exists but uses wrong JWT logic. `organizations` creation exists but models drift from DB.
**Priority:** Critical
