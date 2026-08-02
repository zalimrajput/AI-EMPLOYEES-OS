# AI Employee OS — Database Development Plan & Correctness Report

> **Scope:** Backend/Database only (group project — backend developer role).
> This document (1) compares the product description with the current Supabase schema, (2) audits database correctness, and (3) provides a step-by-step development plan to make the database production-ready.
>
> **Audited:** July 31, 2026 · Schema source: `supabase/migrations/` (36 migrations, 63 tables)

---

## 1. Executive Summary

The current database schema (36 migrations / 63 tables) covers **~85% of the product's data requirements** — multi-tenancy, CRM, quotations, invoices, payments, email, WhatsApp, meetings, documents, knowledge base, tasks, workflows, HR, finance, inventory, marketing, reporting, billing/subscriptions, usage, API keys, security (MFA/SSO), storage, audit logs, AI employees/memory/conversations, and organization settings. The `plans` table even comes pre-seeded with the exact Basic/Pro/Business pricing from the product description.

**However, the database is NOT production-ready.** Critical gaps and errors exist:

| Severity | Issue | Count |
|----------|-------|-------|
| 🔴 Critical | Missing core tables (`roles`, `leads`, `pipelines`+`pipeline_stages`, `quotation_items`, `invoice_items`, `reminders`, `activities`, `user_roles`) | 8 |
| 🔴 Critical | **No `GRANT` statements** — anon/authenticated roles cannot read/write *any* table | All tables |
| 🔴 Critical | RLS enabled on only **8 of 63** tables | 55 uncovered |
| 🟠 High | 9 business tables lack `organization_id` (tenant leak / RLS complexity) | 9 |
| 🟠 High | No signup trigger → new `auth.users` never create a `public.users` row | Auth flow |
| 🟠 High | Money columns use inconsistent `NUMERIC` (unscaled) vs `NUMERIC(12,2)` | ~10 columns |
| 🟠 High | Missing indexes on many FK/org columns | 20+ |
| 🟠 High | `knowledge_articles.embedding` has **no vector index** (documents & ai_memories do) | 1 |
| 🟡 Medium | Inconsistent `updated_at`, no `deleted_at` soft-deletes, plaintext integration tokens | various |
| 🔴 Critical (backend) | SQLAlchemy `User` model (email/password_hash) **does not match** the DB `users` table (FK to `auth.users`) | — |

**Bottom line:** The schema structure and domain coverage are solid. The work needed is **correctness hardening + gap-closing migrations** (037+), **grants + RLS for all tables**, and **aligning backend models to the DB** (that part is for the backend API dev, but the DB must be the single source of truth).

---

## 2. Current Database Inventory (63 tables)

### 2.1 Core & Multi-Tenancy
`organizations` · `users` · `departments` · `organization_settings` · `integrations`

### 2.2 AI Systems
`ai_employees` · `ai_conversations` · `ai_messages` · `ai_memories` · `knowledge_articles`

### 2.3 CRM & Sales
`customers` · `deals` · `products` · `quotations` · `invoices` · `payments`

### 2.4 Communication
`email_threads` · `emails` · `whatsapp_contacts` · `whatsapp_messages`

### 2.5 Productivity
`tasks` · `meetings` · `documents` · `workflows` · `notifications`

### 2.6 HR & AI-HR
`employees` · `attendance` · `leave_requests` · `job_candidates`

### 2.7 Finance & AI-Finance
`expense_categories` · `expenses` · `budgets` · `financial_reports`

### 2.8 Inventory & Procurement
`warehouses` · `suppliers` · `inventory_items` · `stock_movements` · `purchase_orders`

### 2.9 Marketing
`marketing_campaigns` · `audience_segments` · `marketing_content` · `email_campaigns`

### 2.10 Reporting & Analytics
`dashboards` · `reports` · `analytics_events` · `business_metrics`

### 2.11 Billing, Usage & Access
`plans` · `subscriptions` · `billing_transactions` · `usage_records` · `storage_usage` · `api_usage` · `api_keys` · `webhooks` · `api_requests`

### 2.12 Security & Audit
`user_sessions` · `mfa_settings` · `sso_connections` · `security_events` · `audit_logs`

### 2.13 Storage
`storage_files` · `storage_quotas` · `file_access_permissions`

---

## 3. Product Description vs. Current Schema (Feature Coverage Matrix)

| Product Feature (from spec) | DB Support | Status | Notes |
|---|---|---|---|
| AI Executive Assistant | `ai_employees`, `ai_conversations`, `ai_messages`, `ai_memories`, `knowledge_articles` | ✅ | Conversations + memory (vector) present |
| AI Email Assistant (draft/reply/summarize/classify/prioritize/follow-up) | `email_threads` (ai_priority, summary), `emails` (ai_generated) | ✅ | Classification → use `metadata` JSONB |
| AI WhatsApp Assistant | `whatsapp_contacts`, `whatsapp_messages` (media JSONB, direction) | ✅ | Voice via `media` JSONB |
| AI CRM — customer mgmt | `customers` | ✅ | |
| AI CRM — **lead management** | ❌ **No `leads` table** | 🔴 **MISSING** | Backend `lead.py` model exists; no table |
| AI CRM — sales pipeline | `deals` (stage TEXT) | ⚠️ Partial | No `pipelines` entity; stage is free-text on `deals` |
| AI CRM — activity timeline | ❌ | 🔴 **MISSING** | Only `audit_logs`/`analytics_events` exist |
| AI CRM — AI customer summaries/insights | `customers.notes`, `metadata`? | ⚠️ Partial | No `ai_summary` column on `customers` |
| Quotation generator (PDF, tax, discount, branding) | `quotations` (subtotal/tax/discount/total/pdf_url) | ⚠️ Partial | **No line items table** — cannot store "25 laptops" detail |
| Invoice generator (payment tracking, due-date reminders, recurring, PDF, QR, payment links) | `invoices` (amount, status, due_date, pdf_url), `payments` | ⚠️ Partial | **No line items, no recurring fields, no QR/payment-link columns** |
| Meeting assistant (transcript, summary, action items) | `meetings` (transcript, summary, action_items JSONB) | ✅ | |
| Document intelligence (OCR, search, Q&A) | `documents` (extracted_text, embedding), `knowledge_articles` (embedding) | ✅ | Missing vector index on `knowledge_articles` |
| Task manager (assignment, priorities, deadlines, **AI reminders**) | `tasks` (assigned_to, priority, status, due_date, ai_created) | ⚠️ Partial | **No `reminders` table** |
| Reporting & analytics | `reports`, `dashboards`, `analytics_events`, `business_metrics`, `financial_reports` | ✅ | |
| Workflow automation | `workflows` (trigger/actions JSONB) | ✅ | |
| AI Employees (permissions, memory, tools) | `ai_employees` (tools, permissions JSONB), `ai_memories` (vector) | ✅ | |
| Pricing plans (Basic/Pro/Business) | `plans` (seeded 19/49/149) + `subscriptions` | ✅ | Seeded data matches spec exactly |
| Usage tracking (AI requests, storage, API) | `usage_records`, `storage_usage`, `api_usage` | ✅ | |
| API access (Business plan) | `api_keys`, `webhooks`, `api_requests` | ✅ | |
| Department-based permissions (Business plan) | `departments` ✅ but **no `roles` table** | 🔴 **MISSING** | Backend `role.py` model exists; no table |
| Audit logs (Business plan) | `audit_logs` | ✅ | |
| SSO / MFA (Business plan) | `sso_connections`, `mfa_settings`, `user_sessions`, `security_events` | ✅ | |
| Storage (1/20/200 GB plans) | `storage_files`, `storage_quotas` (1GB default), `file_access_permissions` | ✅ | |
| **GRANTs / access for app roles** | ❌ | 🔴 **MISSING** | Nothing readable by `anon`/`authenticated` |
| Row-Level Security (all tenants) | RLS on only 8 of 63 tables | 🔴 **INCOMPLETE** | |

**Coverage scorecard:** ✅ 17 · ⚠️ 8 · 🔴 MISSING/INCOMPLETE 9

---

## 4. Database Correctness Audit

### 4.1 🔴 Critical Issues

**C1. No `GRANT` statements (app cannot access anything)**
- `grep -rl 'GRANT' supabase/migrations/` → **zero matches**.
- Supabase's newer default (`auto_expose_new_tables` unset → always-revoke) means the `anon` and `authenticated` roles have **no privileges** on any table.
- **Fix:** Add `0037_grants.sql` granting `USAGE` on schema `public` + `SELECT/INSERT/UPDATE/DELETE` on all tables to `authenticated` (and appropriate read/limited grants for `anon`), plus full access for `service_role`.

**C2. RLS covers only 8 of 63 tables**
- RLS is enabled only on: `organizations`, `users`, `departments`, `ai_employees`, `customers`, `tasks`, `documents`, `storage_files`.
- The other 55 tables (invoices, payments, quotations, deals, ai_conversations, ai_messages, emails, meetings, workflows, all HR/finance/inventory/marketing/billing tables, etc.) have **no RLS and no policies** → cross-tenant data exposure.
- **Fix:** Enable RLS on all tables + tenant-isolation policies using the existing pattern (`organization_id IN (SELECT organization_id FROM users WHERE id = auth.uid())`).

**C3. Missing core tables (required by product spec / backend scaffolding)**
| Missing table | Why it's required | Existing backend file |
|---|---|---|
| `roles` | Business plan "department-based permissions", RBAC | `app/models/role.py` (non-empty) |
| `leads` | "Lead management" in CRM feature | `app/models/lead.py` (empty stub) |
| `pipelines` + `pipeline_stages` | Sales pipeline entity (stage currently free-text) | `app/models/pipeline.py` (empty stub) |
| `quotation_items` | Line items for quotations ("25 laptops") | — |
| `invoice_items` | Line items for invoices | — |
| `reminders` | "Set reminders", "AI reminders", "due date reminders" | — |
| `activities` (activity timeline) | CRM "Activity timeline", AI activity logs | — |
| `user_roles` (or role on users) | RBAC assignment | — |

> **Note:** Most backend model files for these domains (`lead`, `pipeline`, `customer`, `invoice`, `task`, etc.) are **0-byte empty stubs**; only `role.py` has content. The DB must be built first and serve as the single source of truth; backend models should then be written to match the DB.

**C4. No signup trigger (`auth.users` → `public.users`)**
- `users.id` references `auth.users(id)`, but no trigger/function creates the `public.users` row when a user signs up via Supabase Auth.
- **Fix:** `handle_new_user()` trigger on `auth.users` INSERT → insert into `public.users` (id, organization_id nullable initially; org assigned on org creation).

**C5. Backend SQLAlchemy `User` model does not match the DB**
- DB: `users(id → auth.users, organization_id, full_name, avatar_url, phone, status, ...)` — **no `email`, no `password_hash`** (auth delegated to Supabase).
- Backend: `User(email UNIQUE NOT NULL, password_hash NOT NULL, id uuid4 default)`.
- **Fix (backend dev scope):** update the Python model to match the DB. The DB design (Supabase Auth) is the correct architecture; do not add `password_hash` to the DB.

### 4.2 🟠 High Issues

**H1. 9 business tables lack `organization_id` (tenant resolution)**
| Table | Tenant path |
|---|---|
| `payments` | via `invoice_id` → org |
| `emails` | via `thread_id` → org |
| `whatsapp_messages` | via `contact_id` → org |
| `notifications` | via `user_id` → org |
| `attendance` | via `employee_id` → org |
| `leave_requests` | via `employee_id` → org |
| `mfa_settings` | via `user_id` → org |
| `file_access_permissions` | via `file_id` → org |
| `ai_messages` | via `conversation_id` → org |

RLS policies would require multi-hop JOINs. **Recommendation:** add `organization_id` to these tables (denormalized, backfilled), which makes policies uniform, simpler, and faster. (Tables without a direct parent — `plans`, `organizations` — are correctly excluded.)

**H2. Money columns inconsistent / unscaled**
- `NUMERIC` (unscaled): `deals.value`, `products.price`, `quotations.subtotal/tax/discount/total`, `invoices.amount`, `payments.amount`, `job_candidates.ai_score`.
- `NUMERIC(12,2)` / `NUMERIC(10,2)`: `expenses.amount`, `budgets.amount`, `purchase_orders.total_amount`, `marketing_campaigns.budget`, `plans.price_*`, `billing_transactions.amount`.
- **Fix:** standardize all money to `NUMERIC(12,2)` (or `NUMERIC(14,2)` for totals) with `CHECK (x >= 0)` where appropriate.

**H3. Missing indexes on FK/org columns (20+)**
Examples: `quotations(customer_id)`, `quotations(organization_id)`, `invoices(customer_id)`, `invoices(organization_id)`, `payments(invoice_id)`, `emails(thread_id)`, `whatsapp_messages(contact_id)`, `meetings(organization_id)`, `knowledge_articles(organization_id)`, `tasks(assigned_to)`, `tasks(created_by)`, `email_threads(ai_priority)`, `deals(organization_id)`, `products(organization_id)`, `notifications(user_id)`, `leave_requests(employee_id)`, `audit_logs(organization_id)`, `subscriptions(plan_id)`, `financial_reports(organization_id)`, `usage_records(organization_id, created_at)`...
- **Fix:** a naming convention `idx_<table>_<col>_idx` and add all in one migration.

**H4. `knowledge_articles.embedding` has no vector index**
- `documents` and `ai_memories` have `ivfflat` indexes; `knowledge_articles` does not → AI Q&A over KB will do full scans.
- **Fix:** `CREATE INDEX knowledge_articles_embedding_idx ON knowledge_articles USING ivfflat (embedding vector_cosine_ops);`

**H5. `VECTOR(1536)` is hardcoded**
- All embedding columns assume 1536 dims (OpenAI `text-embedding-3-small`). If the team switches providers (Gemini/Claude embeddings), this must change. Note in plan; keep 1536 unless decided otherwise.

### 4.3 🟡 Medium Issues

- **`updated_at` inconsistency** — present on `organizations`, `users`, `ai_conversations`, `dashboards`, `reports`, `subscriptions`, `organization_settings`, `storage_files`/`storage_quotas`/`inventory_items` — missing on most others. Add to tables that mutate.
- **No soft-delete (`deleted_at`)** anywhere — fine for v1, decide policy later.
- **Integration tokens in plaintext** (`integrations.access_token/refresh_token`, `webhooks.secret`, `sso_connections.client_secret`) — at minimum document that the API layer must encrypt, or store hashes.
- **No `CHECK` constraints on status/priority/direction fields** — free-text everywhere. Acceptable for flexibility, but add CHECKs for critical ones (`ai_messages.role` already has one — good pattern to extend).
- **`storage_quotas.max_storage_bytes` default is 1GB** — must be set from the org's plan (Basic=1GB, Pro=20GB, Business=200GB). Add a function/trigger or compute at API layer.
- **`deals.stage`, `quotations.status`, `invoices.status`, `subscriptions.status`** — consider PG `ENUM` or CHECKs for consistency.
- **`payments` has no `customer_id`** — add it (redundant but speeds reporting) or rely on invoice join.

---

## 5. Database Development Plan (Migrations 0037+)

All changes as **new numbered migrations** in `supabase/migrations/` (never edit applied migrations). Each step is independently testable.

### Phase A — Access & Security (prereq for everything)
- **0037_grants.sql** — GRANT schema usage + table privileges to `anon`, `authenticated`, `service_role`.
- **0038_rls_full.sql** — Enable RLS on all remaining tables; add tenant-isolation policies using a shared helper:
  ```sql
  -- helper: org of current user
  CREATE OR REPLACE FUNCTION public.current_org_id()
  RETURNS UUID LANGUAGE sql STABLE SECURITY DEFINER AS $$
    SELECT organization_id FROM public.users WHERE id = auth.uid()
  $$;
  ```
  Policy pattern per table:
  ```sql
  ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
  CREATE POLICY invoices_tenant_isolation ON invoices
    FOR ALL USING (organization_id = public.current_org_id());
  ```
- **0039_signup_trigger.sql** — `handle_new_user()` trigger on `auth.users` → insert `public.users` row (id, status='active').

### Phase B — Missing core tables (aligns backend models that already exist)
- **0040_roles.sql** — `roles` (id, organization_id, name, permissions JSONB, created_at) + `user_roles` (user_id, role_id, unique) + indexes. *(Backend `role.py` exists.)*
- **0041_leads.sql** — `leads` (id, organization_id, name, email, phone, company, source, status, score, assigned_to, converted_customer_id, metadata, created_at) + indexes. *(Backend `lead.py` exists.)*
- **0042_pipelines.sql** — `pipelines` (id, organization_id, name, is_default, stages JSONB, created_at) + `deals.pipeline_id` FK; backfill default pipeline; index. *(Backend `pipeline.py` exists.)*
- **0043_reminders.sql** — `reminders` (id, organization_id, user_id, target_type, target_id, remind_at, message, channel, triggered, created_at) + index on `(organization_id, triggered, remind_at)`.

### Phase C — Line items & invoicing (core business value)
- **0044_quotation_items.sql** — `quotation_items` (id, quotation_id FK CASCADE, product_id, description, quantity INT, unit_price NUMERIC(12,2), tax_rate NUMERIC(5,2), discount NUMERIC(12,2), line_total NUMERIC(12,2), sort_order).
- **0045_invoice_items.sql** — `invoice_items` (same structure, FK to `invoices`).
- **0046_invoice_extensions.sql** — add to `invoices`: `recurrence_interval INT`, `recurrence_period TEXT`, `next_billing_date DATE`, `payment_link_url TEXT`, `qr_code_url TEXT`, `ai_summary TEXT`; add `customers.ai_summary` too. Standardize money columns to `NUMERIC(12,2)` + CHECKs.
- **0047_activities.sql** — `activities` (id, organization_id, user_id, entity_type, entity_id, action, metadata JSONB, created_at) — CRM activity timeline + AI action log; index `(organization_id, entity_type, entity_id)`.

### Phase D — Tenancy & indexes (correctness hardening)
- **0048_tenant_columns.sql** — add `organization_id` to: `payments`, `emails`, `whatsapp_messages`, `notifications`, `attendance`, `leave_requests`, `mfa_settings`, `file_access_permissions`, `ai_messages`; backfill from parents; set NOT NULL where possible.
- **0049_indexes.sql** — add all missing FK/org/query indexes (see §4.2 H3 list) following `idx_<table>_<col>_idx`.
- **0050_kb_vector_index.sql** — `knowledge_articles_embedding_idx` (ivfflat cosine).

### Phase E — Consistency & validation
- **0051_constraints.sql** — `updated_at` columns on mutating tables; CHECK constraints for money ≥ 0, `quantity ≥ 0`, status enums where decided; `subscriptions.plan_id` NOT NULL; `deals.customer_id` NOT NULL where mandatory.
- **0052_usage_defaults.sql** — function `public.apply_plan_defaults()` (sets `storage_quotas.max_storage_bytes` from plan on subscription change) + trigger; `usage_records` partitioning/index strategy for growth.

---

## 6. Verification Plan (Database Correctness Checks)

Run after each phase (document results in this repo's `supabase/schema_check.sql` — currently empty):

1. **Migrate cleanly:** `supabase db reset` or `supabase migration up` → all 36+ migrations apply with no errors.
2. **Access check:** As `authenticated` role, run `SELECT * FROM invoices LIMIT 1;` → must succeed (validates GRANTs).
3. **RLS check:** `SET ROLE anon;` → `SELECT * FROM invoices;` → 0 rows (or denied), never cross-tenant rows.
4. **Signup check:** create a Supabase auth user → `public.users` row auto-created.
5. **Tenancy check:** two orgs; verify org A user cannot see org B rows in every RLS-covered table (scripted test).
6. **Index check:**
   ```sql
   SELECT tablename, indexname FROM pg_indexes WHERE schemaname='public' ORDER BY 1;
   ```
   → every FK column has an index.
7. **FK integrity:** run a full `pg_catalog` query listing FK constraints with no matching index; and:
   ```sql
   SELECT count(*) FROM quotations q LEFT JOIN customers c ON q.customer_id=c.id WHERE c.id IS NULL;
   ```
8. **Vector check:** `\d knowledge_articles` shows the ivfflat index; a `<=>` query on `ai_memories` uses it (`EXPLAIN`).
9. **Money check:** every money column is `NUMERIC(12,2)` with `>= 0` CHECK.
10. **Seeded plans:** `SELECT name, price_monthly, max_users, ai_requests_limit, storage_limit_gb FROM plans;` → 19/1/500/1, 49/5/10000/20, 149/NULL/NULL/200.

---

## 7. Recommended Conventions (for the whole team going forward)

- **DB is the single source of truth.** SQLAlchemy models mirror the migrations; never `create_all`.
- **Migrations are append-only**; one numbered file per change; never edit applied files.
- **Every tenant table has `organization_id`** (UUID, FK → organizations, ON DELETE CASCADE, NOT NULL, indexed).
- **Money = `NUMERIC(12,2)`** with `CHECK (x >= 0)`.
- **IDs = `UUID DEFAULT gen_random_uuid()`** everywhere.
- **Timestamps:** `created_at` (all tables) + `updated_at` (mutating tables), both `TIMESTAMPTZ DEFAULT NOW()`.
- **Index naming:** `idx_<table>_<column>_idx`; index every FK and every org column.
- **RLS:** every table enabled, policy = `organization_id = current_org_id()` (helper function), plus GRANTs in the same migration.
- **AI:** embeddings `VECTOR(1536)` (decide once), ivfflat cosine index on every embedding column.

---

## 8. Open Decisions (need team confirmation)

1. **Auth model** — confirm Supabase Auth as the only auth system (recommended). Backend JWT must verify Supabase tokens; drop local `password_hash` concepts.
2. **Embedding provider/dimension** — 1536 (OpenAI) vs Gemini/Claude dimensions → affects `VECTOR(n)` columns.
3. **Soft deletes** — include `deleted_at` everywhere or not in v1.
4. **Enums vs TEXT+CHECK** for status fields — recommend CHECKs for consistency without migration friction.
5. **Multi-currency** — `organization_settings.currency` exists; money columns stay per-org currency (no FX table in v1).

---

*Prepared from a full audit of `supabase/migrations/` (all 36 files), backend model inventory, and the product description. No source files were modified to produce this document.*
