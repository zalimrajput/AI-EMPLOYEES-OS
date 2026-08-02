# AI Employee OS

**AI Employee OS** is a multi-tenant SaaS platform where one application and one database securely support **unlimited organizations**. Each organization has its own isolated users, departments, customers, CRM, quotations, invoices, documents, reports, AI employees, and settings.

Visitors create their own organization from the main website (self-service); the first registered user automatically becomes the **Company Admin**. The platform has three login types:

| Type | Login | Sees |
|------|-------|------|
| **Super Admin** | platform admin account | all organizations + their dashboards, subscriptions, modules, AI models, integrations |
| **Org Admin** | company admin account | only their own organization's dashboards (all 13 company dashboards) |
| **User** | employee account | only the dashboards allowed by their assigned role |

> **Super Admin does NOT create organizations.** Companies register themselves from the main website.

---

## 1. Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16 (App Router) · React 19 · TypeScript · Tailwind CSS v4 |
| Backend | Python FastAPI · SQLAlchemy · Pydantic |
| Database | PostgreSQL (Supabase, multi-tenant) |
| Auth | Supabase Auth (email/password + OAuth Google/Microsoft) · JWT |
| Realtime/Jobs | Celery · Redis · WebSockets |
| AI | OpenAI · Anthropic · Gemini (via OpenRouter), pgvector RAG, agents |
| Storage | Supabase Storage / S3-compatible |

---

## 2. Architecture

```
┌──────────────────────────┐      ┌──────────────────────────┐
│   Frontend (Next.js)     │      │   Backend (FastAPI)      │
│   http://localhost:3000  │◄────►│   http://localhost:8000  │
│   src/app + components   │ JWT  │   app/api/v1 (29 routers)│
└──────────┬───────────────┘      └───────────┬──────────────┘
           │                                 │
           └───────────────┬─────────────────┘
                           ▼
                ┌──────────────────────────┐
                │  Supabase (PostgreSQL)   │
                │  71+ tables · RLS on all │
                │  64 migrations           │
                └──────────────────────────┘
```

- **Frontend** talks to Supabase directly (auth session, reads via supabase-js) and to FastAPI for business logic (CRUD endpoints protected by Supabase JWTs).
- **Backend** uses the Supabase service-role key for user provisioning (admin API) and writes via SQLAlchemy (superuser connection, bypasses RLS).
- **Tenancy** is enforced by Postgres **Row Level Security** (`organization_id = current_org_id()`) on every table.

---

## 3. Database (Supabase — `supabase/migrations/`)

### 3.1 Migrations (64 total, 0001–0064)

| Range | Purpose |
|-------|---------|
| 0001–0020 | Core tables: extensions, organizations, users, departments, AI employees, memory, integrations, CRM, sales pipeline, products, quotations, invoices, payments, email, WhatsApp, tasks, meetings, documents, knowledge base, workflows |
| 0021–0036 | Notifications, audit logs, HR-AI, finance-AI, inventory-AI, marketing-AI, reporting/analytics, billing/subscriptions, usage tracking, API keys, MFA/SSO, storage, RLS baseline, AI conversations/messages, organization settings |
| 0037–0046 | Grants, tenant columns backfill, indexes, signup trigger, roles + user_roles (RBAC), leads, pipelines, reminders, quotation items, invoice items |
| 0047–0051 | Invoice extensions (recurrence, payment links, QR, AI summary), activities timeline, KB vector index, constraints, plan-driven storage defaults |
| 0052–0058 | **Full RLS on all 71 tables**, org creation + self-update flow, security fixes, signup fixes, **local password auth removed** (Supabase Auth is the single source of truth) |
| 0059 | Seed default roles (Owner/Admin/Employee) + org-creation trigger |
| 0060 | **Platform layer**: Super Admin (`platform_roles`), full **11 company roles**, **12 AI employees**, **14 dashboards** + `dashboard_role_access` per org |
| 0061 | Tenancy indexes + anon hardening |
| 0062 | `org_modules` (module enablement by Super Admin + Org Admin), plan/status columns, Super Admin cross-tenant visibility |
| 0063 | `modules` + `widgets` catalog seeds |
| 0064 | Super Admin RLS extension for AI employees + integrations |

### 3.2 Key Tables by Module

| Module | Tables |
|--------|--------|
| Platform | `platform_roles`, `platform_settings`, `platform_logs`, `plans`, `subscriptions`, `billing_transactions` |
| Organizations | `organizations`, `organization_settings`, `departments` (membership lives on `users.organization_id`) |
| Users & RBAC | `users`, `roles`, `user_roles`, `platform_roles`, `user_sessions`, `mfa_settings`, `security_events` |
| AI Employees | `ai_employees`, `ai_conversations`, `ai_messages`, `ai_memories`, `ai_requests` |
| CRM | `customers`, `leads`, `deals`, `pipelines`, `activities`, `products` |
| Quotations | `quotations`, `quotation_items` |
| Invoices | `invoices`, `invoice_items`, `payments`, `reminders` |
| Email | `email_threads`, `emails`, `email_campaigns` |
| WhatsApp | `whatsapp_contacts`, `whatsapp_messages` |
| Meetings | `meetings`, `attendance` |
| Documents | `documents`, `knowledge_articles`, `file_access_permissions`, `storage_files`, `storage_quotas` |
| Tasks & Workflows | `tasks`, `workflows`, `notifications` |
| HR | `employees`, `leave_requests`, `job_candidates` |
| Finance | `expense_categories`, `expenses`, `budgets`, `financial_reports` |
| Inventory | `inventory_items`, `warehouses`, `suppliers`, `purchase_orders`, `stock_movements` |
| Marketing | `marketing_campaigns`, `campaigns`, `audience_segments`, `marketing_content` |
| Operations | `api_keys`, `webhooks`, `api_requests`, `audit_logs`, `usage_records`, `api_usage` |

### 3.3 Roles (12 human roles)

**1 Platform role:** Super Admin · **11 Company roles:** Company Admin, CEO / Executive, Sales Manager, Sales Executive, HR Manager, Finance Manager, Accountant, Customer Support, Marketing Manager, Operations Manager, Employee/User.

Each organization gets all 11 company roles seeded on creation (`seed_default_roles` trigger). Legacy orgs also keep `Owner`/`Admin`/`Employee` rows (mapped to the new model by `normalize()` in the frontend).

### 3.4 AI Employee Roles (12 per company)

AI Executive Assistant, AI Sales Assistant, AI Customer Support Agent, AI HR Assistant, AI Recruiter, AI Finance Assistant, AI Accountant, AI Marketing Assistant, AI Content Writer, AI Legal Assistant, AI Inventory Manager, AI Procurement Assistant — each with its own tools + permissions (`seed_default_ai_employees`).

### 3.5 Dashboards (14 seeded per company)

Super Admin, Company Admin, CEO / Executive, Sales, CRM, HR, Finance, Customer Support, Marketing, Operations, Employee, AI Employees, Reports & Analytics, Settings & Integrations — mapped to roles via `dashboard_role_access` and to modules via `dashboards.name` ↔ `modules.dashboard`.

### 3.6 Security & Tenancy

- **RLS enabled on all 71 tables** with `organization_id = public.current_org_id()` (SECURITY DEFINER helper reads the caller's org from `users.organization_id`).
- **Super Admin** bypasses tenancy via `is_super_admin()` (cross-tenant reads, module control).
- **No tenant-hopping:** a user cannot change their own `organization_id` (WITH CHECK constraint, migration 0054).
- Grants for `anon` / `authenticated` / `service_role` set via migration 0037 + default privileges.
- Passwords are **never stored locally** — Supabase Auth owns credentials; the backend provisions auth users via the Admin API with `email_confirm: true`.

---

## 4. Backend (FastAPI — `backend/app/`)

### 4.1 Structure

```
backend/app/
├── main.py                 # FastAPI app, CORS, mounts /api/v1
├── api/v1/                 # 29 route modules (below)
│   ├── router.py           # registers every router
│   ├── auth/routes.py      # POST /auth/login (Supabase GoTrue)
│   ├── users/routes.py     # create/list/delete users (org admin)
│   ├── organizations/      # create org (self-service)
│   ├── modules/            # module catalog + per-org module control
│   └── ... (24 more modules)
├── core/                   # config, auth (JWT verify), database, permissions, validators
├── middleware/             # audit, auth, rate-limit, request context, tenant
├── models/                 # SQLAlchemy models (mirror the DB)
├── schemas/                # Pydantic request/response schemas
├── services/               # business logic (user, org, crm, invoice, billing…)
├── repositories/           # data access layer
├── ai/                     # AI engine: agents, orchestrator, planner, memory, RAG, tools
├── rag/                    # chunking, ingestion, ranking, search, vector store
├── integrations/           # gmail, outlook, whatsapp, google_calendar, microsoft365, stripe, slack, accounting
├── workers/                # celery tasks (ai, email, document, notification, report, whatsapp, embedding)
└── utils/                  # pdf, encryption, files, email helpers
```

### 4.2 API Endpoints (all under `/api/v1`)

Auth & platform:
- `POST /auth/login` · `POST /organizations/` · `GET /users/` · `POST /users/` · `DELETE /users/{user_id}` · `GET /modules/` · `GET /modules/org/{organization_id}` · `PATCH /modules/org/{organization_id}/{module_key}` · `PATCH /modules/me/{module_key}` · `GET /organization-settings/` · `PATCH /organization-settings/` · `GET /departments/` · `POST /departments/`

AI:
- `GET /ai-employees/` · `POST /ai-employees/` · `GET|PATCH|DELETE /ai-employees/{item_id}` · `GET|POST /ai-conversations/` · `GET|POST /ai-messages/` · `GET|POST /ai-memories/` · `GET|POST /ai-chat/conversations` · `GET /ai-chat/conversations/{id}/messages` · `POST /ai-chat/messages`

Business (each with `GET /` + `POST /` + `GET|PATCH|DELETE /{item_id}` unless noted):
- `customers` · `leads` · `deals` · `pipelines` · `products` · `quotations` · `quotation-items` · `invoices` · `invoice-items` · `payments` · `reminders` · `activities`
- `emails` · `email-threads` · `email-campaigns` · `whatsapp-contacts` · `whatsapp-messages` · `meetings` · `documents` · `knowledge` / `knowledge-articles`
- `tasks` · `workflows` · `employees` · `attendance` · `leave-requests` · `candidates` · `expenses` · `expense-categories` · `budgets`
- `inventory-items` · `warehouses` · `suppliers` · `purchase-orders` · `stock-movements` · `campaigns` · `audience-segments` · `marketing-content`
- `integrations` · `api-keys` · `api-requests` · `webhooks` · `storage-files` · `storage-quotas` · `billing/plans` · `billing/subscriptions` · `billing/transactions`
- `GET /analytics/summary`

> Full interactive docs at `http://localhost:8000/docs` (Swagger UI).

### 4.3 Auth Flow

1. **Frontend** calls `supabase.auth.signInWithPassword` (email/password) or the backend `POST /api/v1/auth/login` (Supabase GoTrue grant_type=password). Both return Supabase access + refresh tokens.
2. **Backend** verifies JWTs via `app/core/auth.py` (`get_current_user`) and the Supabase JWT secret.
3. **User provisioning:** org admins call `POST /api/v1/users/` → the backend creates the Supabase Auth user (Admin API, service-role key, `email_confirm: true`) and assigns the requested role via `user_roles`.

---

## 5. Frontend (Next.js — `frontend/src/`)

### 5.1 Pages

| Route | Page |
|-------|------|
| `/` | Landing page (hero, features, pricing, testimonials, workflow demo, CTA) |
| `/login` | Login (email/password + Google/Microsoft OAuth + **demo role selector**) |
| `/register` | Self-service **Create workspace** (visitor becomes Company Admin) |
| `/dashboard` | Company Admin dashboard (module widgets) |
| `/dashboard/super-admin` | **Super Admin dashboard** (all orgs, plans, modules, tenant control) |
| `/dashboard/super-admin/org/[orgId]` | Org dashboard picker (13 company dashboards) |
| `/dashboard/super-admin/org/[orgId]/[dashboardId]` | Full-screen org dashboard view |
| `/dashboard/{executive,sales,crm,hr,finance,support,marketing,operations,employee}` | Role dashboards |
| `/dashboard/employees` + `/dashboard/employees/[id]` | AI employees |
| `/dashboard/tasks` · `/dashboard/workflows` · `/dashboard/analytics` · `/dashboard/chat` · `/dashboard/billing` · `/dashboard/settings` | Main-nav modules |

### 5.2 Role-Based Access Control

| File | Role |
|------|------|
| `lib/roles.ts` | Role constants (12), `primaryRole()`, `isAdmin()`, `homePathForRoles()` (login landing per role) |
| `lib/dashboards.ts` | 14-dashboard registry; `dashboardsForRoles()` — Super Admin → all 14, Company Admin/CEO → 13, department roles → their own |
| `lib/modules.ts` | 20+ module catalog with widgets; `isModuleEnabled()`, `dashboardsForModules()`, `navForModules()` |
| `app/(app)/layout.tsx` | Layout guard: redirects users away from dashboards their role/modules don't allow |
| `components/layout/sidebar.tsx` | Role-scoped nav + **Dashboards** section (Super Admin → single link; Org Admin → 13; users → their role's) |

### 5.3 Data Services

- `services/data.ts` — org stats, tasks (backend-first with demo fallback)
- `services/business.ts` — customers, leads, quotations, invoices, meetings (backend-first with curated demo fallback)
- `services/admin.ts` — platform orgs/overview (super admin), org modules/members/roles/departments (org admin), invite/delete users
- `lib/api/client.ts` — typed API client for all backend endpoints (JWT attached)
- `lib/api/types.ts` — shared TS types
- `hooks/use-session.ts` — Supabase session, profile, roles, enabled modules

### 5.4 Key UI Components

`components/auth/` (login + register forms with demo logins) · `components/dashboard/` (stat cards, charts, activity feed, module widgets) · `components/layout/` (sidebar, navbar, mobile nav) · `components/ui/` (button, card, input, badge, tabs, skeleton…) · `components/landing/` (marketing sections) · `components/tasks/kanban.tsx`

---

## 6. Demo Logins (seeded — `backend/scripts/seed_demo_users.py`)

| Role | Email | Password | What you see |
|------|-------|----------|--------------|
| **Super Admin** | `superadmin@demo.com` | `SuperAdmin@123` | All orgs + platform management |
| **Org Admin** | `orgadmin@demo.com` | `OrgAdmin@123` | Demo Company — all 13 dashboards |
| **Employee** | `employee@demo.com` | `Employee@123` | Demo Company — role-based dashboard only |

The login page has a **"Try a demo role"** selector that signs in with one click.

> ⚠️ Demo passwords are intentionally public for testing — **rotate or remove before production.**

---

## 7. Running the Project

### Backend

```bash
cd backend
# configure .env (DATABASE_URL, SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_JWT_SECRET)
uvicorn app.main:app --reload        # http://localhost:8000  (docs at /docs)
```

### Frontend

```bash
cd frontend
npm install
npm run dev                          # http://localhost:3000
```

### Database

```bash
cd supabase
supabase db push                     # apply migrations to the remote project
supabase migration list
```

### Seed demo users

```bash
cd backend
python -m scripts.seed_demo_users
```

### Validate

```bash
cd frontend && npx tsc --noEmit && npm run lint   # zero errors/warnings expected
```

---

## 8. Module Library (enable/disable per org)

The Super Admin enables/disables modules per organization (from the Super Admin dashboard → "Modules"); the Org Admin can further switch them off for their workspace but cannot enable a module the platform admin disabled. Each module powers one dashboard and a set of widgets.

| # | Module | Dashboard |
|---|--------|-----------|
| 1 | Organization Management | Company Admin |
| 2 | User & Role Management | Company Admin |
| 3 | Authentication & Security | Company Admin |
| 4 | AI Executive Assistant | CEO / Executive |
| 5 | AI Employees | AI Employees |
| 6 | Email Management | Customer Support |
| 7 | WhatsApp Communication | Customer Support |
| 8 | CRM | CRM |
| 9 | Quotation Management | Sales |
| 10 | Invoice & Payments | Finance |
| 11 | Meetings & Calendar | Operations |
| 12 | Document Intelligence | Operations |
| 13 | Task Management | Employee |
| 14 | Workflow Automation | Operations |
| 15 | Reporting & Analytics | Reports & Analytics |
| 16 | Integrations | Company Admin |
| 17 | Notifications | All dashboards |
| 18 | Audit Logs | Company Admin |
| 19 | HR & People | HR |
| 20 | Marketing | Marketing |
| 21 | Operations | Operations |
| 22 | Customer Support | Customer Support |
| 23 | Billing | Company Admin |
| 24 | Settings | Settings & Integrations |
| 25 | Overview *(always on)* | Company Admin |

---

## 9. Related Documents

- `DATABASE_COMPLETION.md` — detailed DB alignment report (migrations 0037–0058)
- `PROJECT_ANALYSIS.md` — product analysis
- `DATABASE_DEVELOPMENT_PLAN.md` — database development plan
- `supabase/schema_check.sql` — schema verification queries
