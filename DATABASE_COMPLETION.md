# AI Employee OS — Database Alignment: Completion Report

> **What happened:** The Supabase database has been fully aligned with the product description (AI Employee OS) and **22 new migrations (0037–0058) were created and pushed to the remote database** via `supabase db push`. Local password auth was removed — Supabase Auth is now the single source of truth.
>
> **Remote project:** `ai employees os` (`kxddbnybzfwwmjtrosyb`, PostgreSQL 17, Singapore) · **Date:** July 31, 2026

---

## 1. Summary

| Metric | Before | After |
|--------|--------|-------|
| Migrations | 36 | **58** |
| Tables | 63 | **71** |
| RLS-enabled tables | 8 | **71** (all) |
| `GRANT` statements | 0 | ✅ full grants for anon/authenticated/service_role |
| Missing core tables (roles, leads, pipelines, reminders, line items, activities) | 8 missing | ✅ all created |
| Tables missing `organization_id` | 9 | ✅ all added + backfilled |

The database now matches the product description end-to-end: CRM with leads + pipelines + activity timeline, line-item quotations/invoices, recurring invoices + payment links + QR codes, AI reminders, RBAC, signup automation, plan-driven storage quotas, and full multi-tenant security.

---

## 2. New Migrations (0037–0052)

| # | File | Purpose |
|---|------|---------|
| 0037 | `0037_grants.sql` | GRANT schema usage + SELECT (anon) / ALL (authenticated, service_role) on all tables + default privileges |
| 0038 | `0038_tenant_columns.sql` | Add `organization_id` to 9 child tables (payments, emails, whatsapp_messages, notifications, attendance, leave_requests, mfa_settings, file_access_permissions, ai_messages) + backfill from parents |
| 0039 | `0039_indexes.sql` | ~30 missing indexes on FK/org/query columns |
| 0040 | `0040_signup_trigger.sql` | `handle_new_user()` trigger on `auth.users` → auto-creates `public.users` row; makes `users.organization_id` nullable (pre-org); `users_self_access` SELECT policy |
| 0041 | `0041_roles.sql` | `roles` + `user_roles` tables (RBAC / department-based permissions) |
| 0042 | `0042_leads.sql` | `leads` table (CRM lead management) |
| 0043 | `0043_pipelines.sql` | `pipelines` table + `deals.pipeline_id` FK |
| 0044 | `0044_reminders.sql` | `reminders` table (AI reminders / due-date follow-ups) |
| 0045 | `0045_quotation_items.sql` | `quotation_items` line items + org backfill |
| 0046 | `0046_invoice_items.sql` | `invoice_items` line items + org backfill |
| 0047 | `0047_invoice_extensions.sql` | Invoices: `recurrence_*`, `next_billing_date`, `payment_link_url`, `qr_code_url`, `ai_summary`; customers: `ai_summary`, `status`, `updated_at`; money columns standardized to `NUMERIC(12,2)` |
| 0048 | `0048_activities.sql` | `activities` table (CRM activity timeline / AI action log) |
| 0049 | `0049_kb_vector_index.sql` | Missing ivfflat vector index on `knowledge_articles.embedding` |
| 0050 | `0050_constraints.sql` | `updated_at` on 15 tables + CHECK constraints (non-negative money/quantity) |
| 0051 | `0051_usage_defaults.sql` | `apply_plan_defaults()` trigger → sets `storage_quotas.max_storage_bytes` from plan on subscription change |
| 0052 | `0052_rls_full.sql` | `current_org_id()` SECURITY DEFINER helper; drops legacy recursive 0033 policies; **RLS + tenant-isolation policies on all 71 tables**; plans readable catalog |
| 0053 | `0053_org_creation_and_self_update.sql` | Org creation flow (`organizations_create` policy + `set_org_creator` trigger auto-assigns the creator); `users_self_update` policy (org-less users can edit their own profile); neutral signup name fallback |
| 0054 | `0054_fix_users_self_update.sql` | **Security fix:** constrained `users_self_update` WITH CHECK so a user cannot change their own `organization_id` (tenant-hopping prevention); explicit `WITH CHECK` on `users_tenant_isolation` |
| 0055 | `0055_fix_users_notnull_for_signup.sql` | **Signup fix:** dropped `NOT NULL` on `users.email` / `users.password_hash` (live-DB drift from migration 0003) which was breaking the `handle_new_user` signup trigger with a null-value violation |
| 0056 | `0056_fix_org_create_returning.sql` | **Org-create fix:** added `organizations.created_by uuid DEFAULT auth.uid()` and extended the tenant policy to `id = current_org_id() OR created_by = auth.uid()` so `INSERT … RETURNING` (`insert().select()`) no longer 403s (see note 10) |
| 0057 | `0057_drop_local_password_auth.sql` | **Local auth removed:** `DROP COLUMN users.password_hash`; signup trigger now copies `email` from `auth.users` into `public.users.email` |
| 0058 | `0058_drop_users_email_unique.sql` | **Constraint cleanup:** dropped redundant `users_email_key UNIQUE(email)` (Supabase Auth already enforces email uniqueness; legacy rows could otherwise break signups) |

---

## 3. Verification Results (post-push)

Live queries against the remote database confirmed:

- ✅ **8 new tables** exist: `roles`, `user_roles`, `leads`, `pipelines`, `reminders`, `quotation_items`, `invoice_items`, `activities`
- ✅ **`organization_id`** added to all 11 target tables (9 child tables + 2 line-item tables)
- ✅ **`deals.pipeline_id`** + 6 invoice extension columns present
- ✅ **RLS enabled on 71/71 tables** (was 8/63)
- ✅ Functions/triggers present: `current_org_id()`, `handle_new_user()`, `on_auth_user_created`, `apply_plan_defaults()`
- ✅ Migration history ends at `0058`
- ✅ Seeded plans intact: Basic 19 / Pro 49 / Business 149
- ✅ Total tables: 71
- ✅ Grants verified on all 8 new tables (SELECT for anon; SELECT+INSERT for authenticated/service_role)
- ✅ Runtime fixes live: `set_org_creator` trigger, `organizations_create` policy, `users_self_update` policy
- ✅ Tenant-hopping hole closed (0054): `users_self_update` WITH CHECK now requires `organization_id IS NOT DISTINCT FROM current_org_id()`

---

## 4. Correctness Notes & Decisions

1. **Auth model (confirmed):** Supabase Auth is the single source of truth. `users.id` references `auth.users(id)`; the signup trigger creates the profile row. `users.organization_id` is nullable so a user can exist before being assigned to an org.
2. **Legacy RLS fixed:** Migration `0033` had self-referential policies (e.g., `users_isolation` querying `users` from within a `users` policy) → recursive-RLS risk. `0052` drops those and replaces them with non-recursive `current_org_id()` policies.
3. **RLS design:** Every tenant table uses `organization_id = public.current_org_id()` (FOR ALL). `organizations` uses `id = current_org_id()`. `users` additionally keeps `users_self_access` (SELECT where `id = auth.uid()`). `plans` is a global read-only catalog (`USING (true)` SELECT).
4. **Line-item org resolution:** `quotation_items` / `invoice_items` carry their own `organization_id` (backfilled from parent) so RLS works without joins.
5. **Money:** All money columns standardized to `NUMERIC(12,2)`; CHECK constraints prevent negative amounts/quantities.
6. **Deploy note:** The `supabase db push` Docker warning is **non-fatal** — it only affects local migration-catalog caching (Docker is not installed on this machine). The remote push itself succeeded and the migration history is updated.
7. **Org creation flow (0053):** An authenticated user with no org can INSERT an `organizations` row; the `set_org_creator` trigger assigns `users.organization_id` to the new org automatically. `users_self_update` lets any user (including org-less) update their own profile row, while `users_tenant_isolation` still governs access to other users.
8. **Line-item inserts:** `quotation_items` / `invoice_items` policies enforce `organization_id = current_org_id()` on INSERT (via implicit WITH CHECK) — the API must always set `organization_id` on new rows.
9. **Tenant-hopping fix (0054):** `users_self_update` was tightened so a user can update their own profile fields but **cannot change their own `organization_id`** — org assignment only happens through the `set_org_creator` trigger or via `service_role`/backend.
10. **Org-create `RETURNING` fix (0056, verified live):** `POST /rest/v1/organizations` with `Prefer: return=representation` (supabase-js `.insert().select()`) returned **403 “new row violates RLS”**. Root cause (reproduced in raw SQL): `INSERT … RETURNING` output is filtered by the SELECT policy `id = current_org_id()`, and `current_org_id()` reads `users.organization_id` under the **statement snapshot taken before the AFTER trigger runs**, so the creator’s membership is invisible to the `RETURNING` check. A bare INSERT (no RETURNING) passed — hence the 201/403 split. A BEFORE-trigger alternative was tested and **rejected** (nested `UPDATE` hits `users_organization_id_fkey` because the org row doesn’t exist yet). Final fix: `organizations.created_by uuid DEFAULT auth.uid()` + policy `USING (id = current_org_id() OR created_by = auth.uid())` — the policy is evaluated against the NEW row itself, so `RETURNING` is visible while isolation is preserved. Verified: user A creates org (201 + row), sees it; user B sees **no** orgs; each user only ever sees their own. Backend (service_role) inserts get `created_by = NULL` and remain governed by membership — unaffected.
11. **Supabase Auth is now the single auth source (0057–0058, verified live end-to-end):** `users.password_hash` was dropped and the redundant `users_email_key` constraint removed. The signup trigger copies `email` from `auth.users`. Backend reworked: `POST /api/v1/auth/login` calls Supabase GoTrue (`/auth/v1/token?grant_type=password`) and returns the Supabase `access_token` + `refresh_token`; `POST /api/v1/users/` creates the auth user via the Supabase Admin API (`email_confirm: true`, service role key — never returned to clients) and upserts the `public.users` profile row by the auth user id (no password ever stored locally). Verified: create org → 200; create user → 200 with **no `password_hash` in the response**; profile row has org/email/status; login → 200 with tokens; wrong password → 401; the returned token validates against `/auth/v1/user`. Note: 5 legacy rows that had local hashes are now profile-only rows — those users were never in `auth.users`, so they must be re-created via the Admin API to log in again.

---

## 5. Remaining Work (outside this scope)

The database layer is now complete and aligned. What still needs to happen (by the relevant team members):

- **Backend (FastAPI):** Rewrite SQLAlchemy models to mirror the DB (the old `User` model with `email`/`password_hash` does not match; auth must verify Supabase JWTs). Wire routers, fix `requirements.txt`, CORS, etc.
- **AI engine:** All `app/ai/*` modules are empty stubs — model router, agents, orchestration, RAG, tools.
- **Frontend:** Build the actual UI (login, dashboard, chat) — currently boilerplate.
- **Seed test:** Create an org + user in Supabase and confirm RLS isolation works for two different orgs.
- **Re-apply grants to future tables** automatically via the `ALTER DEFAULT PRIVILEGES` set in 0037.

---

## 6. How to Reproduce / Roll Forward

```bash
# Apply remaining local migrations to the linked remote project
cd supabase
supabase db push

# Inspect migration status
supabase migration list
```
