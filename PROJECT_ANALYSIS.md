# AI Employee OS — Project Analysis & Remediation Plan

> **Document purpose:** Deep analysis of the current repository state, identification of all blocking flaws, and a phased, prioritized plan to make the project functional.
>
> **Audited:** July 31, 2026 · Repo root: `E:\ai-employee-os`

---

## 1. Executive Summary

The repository contains the scaffolding of an ambitious full‑stack product — **"AI Employee OS"** — with a FastAPI backend, a Next.js (App Router) frontend, and a Supabase/Postgres schema defined by 36 SQL migrations (63 tables). The directory structure and data model are well thought out and represent a real, coherent product vision (multi‑tenant AI agents for sales, marketing, HR, finance, legal, recruiting, support, inventory, accounting, and executive functions).

**However, the project is currently non‑functional.** Concretely:

| # | Blocker | Impact |
|---|---------|--------|
| 1 | The Python virtualenv contains **only pip/setuptools** — no FastAPI, SQLAlchemy, etc. | Backend cannot even import (`ModuleNotFoundError: fastapi`). |
| 2 | **~95% of backend modules are empty 0‑byte stubs** (all AI agents, AI engine, orchestration, RAG, integrations, workers, realtime, most API routers, most models/schemas, all tests). | The core product — the AI engine — is entirely unwritten. |
| 3 | `api/v1/router.py` registers only **3 of ~28 routers** (`organizations`, `users`, `auth`); even the implemented `health` router is not registered. | Only a handful of endpoints exist. |
| 4 | **Auth architecture conflict:** backend implements its own email/password + JWT flow against a `users` table that *does not match* the Supabase migration (which makes `users.id` a FK to `auth.users(id)` with no `email`/`password_hash` columns). | Two mutually incompatible auth models; login can never succeed against the real schema. |
| 5 | `requirements.txt` is incomplete/broken: `from jose import jwt` but no `python-jose`; `EmailStr` but no `email-validator`; sync SQLAlchemy engine but no `psycopg2`; asyncpg present but unused. | Runtime import/DB errors after install. |
| 6 | `config.py` omits `JWT_ALGORITHM` and `ACCESS_TOKEN_EXPIRE_MINUTES`, both referenced by `jwt.py`. | `AttributeError` on login. |
| 7 | `database.py` prints `settings.DATABASE_URL` to stdout (secret leakage) and duplicates the settings import. | Security + hygiene flaw. |
| 8 | `models/ai_memory.py` contains a **copy‑pasted `AIMessage` class** (wrong file, wrong class name, duplicate model). | Confusing/misleading code; model drift. |
| 9 | Supabase RLS policies cover only 8 of 63 tables, and **no `GRANT` statements exist** for anon/authenticated roles. | The frontend's Supabase client cannot read any table (all denied). |
| 10 | Frontend is a **bare `create-next-app` boilerplate** (landing page + a Supabase connection test). No auth UI, no dashboard, no API client for the backend. | Nothing for users to actually use. |
| 11 | `main.py` has **no CORS middleware**, no lifespan/startup hooks, no exception handlers, no logging. | Frontend (port 3000) → backend (port 8000) calls are blocked by CORS. |
| 12 | `Dockerfile`, `docker-compose.yml`, backend `README.md`, backend `migrations/`, `.dockerignore` are **0 bytes**. No Alembic setup; no container story. | No deployment path. |
| 13 | No seed data / bootstrap script — no way to create the first organization + user + admin. | Dead app out of the box. |
| 14 | Git repo is in a messy intermediate state (root app files deleted, everything else untracked, no commits recorded). | History/review risk. |

**Bottom line:** The *design skeleton* is good and worth keeping — especially the 36 Supabase migrations. The implementation layer (backend logic, AI engine, frontend UI) must be built out; the auth/DB architecture must be reconciled first.

---

## 2. What Exists and What's Missing (Inventory)

### 2.1 What is genuinely implemented

**Backend (only ~15 non‑empty files):**
- `app/main.py` — FastAPI app (minimal, missing CORS/lifespan).
- `app/core/config.py`, `database.py`, `jwt.py`, `security.py`, `validators.py` — base plumbing (with the bugs noted above).
- `app/models/`: `organization.py`, `user.py`, `role.py`, `department.py`, `ai_employee.py`, `ai_conversation.py`, `ai_message.py`, `base.py`, `__init__.py`.
- `app/schemas/`: `user.py`, `organization.py`, `auth.py`.
- `app/services/`: `user_service.py`, `auth_service.py`, `organization_service.py`.
- `app/repositories/`: `user_repository.py`, `organization_repository.py`.
- `app/api/v1/`: `health/routes.py`, `auth/routes.py`, `users/routes.py`, `organizations/routes.py`, `router.py`.
- `app/middleware/request_context.py` — contextvars (unused elsewhere).

**Supabase (the strongest asset):**
- 36 migrations creating 63 tables: multi‑tenant orgs, users, roles, departments, CRM (customers/leads/pipeline), sales (products/quotations), finance (invoices/payments), email, WhatsApp, tasks, calendar, documents, knowledge base, workflows, notifications, audit logs, HR AI, finance AI, inventory AI, marketing AI, reporting/analytics, billing/subscriptions, usage, API keys, MFA/SSO, storage, RLS, AI conversations/messages, organization settings.
- `config.toml` for local Supabase dev.

**Frontend:**
- Next.js 16.2.12 + React 19, Tailwind v4, TypeScript (tsc passes).
- `src/lib/supabase/client.ts` — Supabase browser client.
- `src/app/test/page.tsx` — a Supabase connectivity check.
- `.env.local` with Supabase URL + publishable key.

### 2.2 What is entirely missing (0‑byte stubs)

**The entire AI layer** (the product's core):
- `app/ai/engine.py`, `orchestrator.py`, `planner.py`, `executor.py`, `memory.py`, `retriever.py`, `embeddings.py`, `model_router.py`, `prompts.py`, `guardrails.py`, `evaluation.py`
- All 10 agents: `sales`, `marketing`, `hr`, `finance`, `accountant`, `executive`, `inventory`, `legal`, `recruiter`, `support`
- All 6 tools: `calendar_tools`, `crm_tools`, `document_tools`, `email_tools`, `invoice_tools`, `search_tools`
- Entire `app/rag/` (chunking, ingestion, ranking, search, vector_store)
- Entire `app/integrations/` (accounting, gmail, google_calendar, microsoft365, outlook, slack, stripe, whatsapp)
- Entire `workers/` (celery_app + 7 workers) and `realtime/` (websocket, events, notifications)
- All tests (`tests/*.py` — 5 files, 0 bytes)

**API routers not registered / not implemented (24 modules):**
`ai_chat`, `ai_conversations`, `ai_employees`, `ai_messages`, `analytics`, `api_keys`, `billing`, `calendar`, `crm`, `documents`, `email`, `finance`, `hr`, `integrations`, `inventory`, `knowledge`, `marketing`, `organization_settings`, `sales`, `storage`, `tasks`, `webhooks`, `whatsapp`, `workflows`.

**Models/schemas missing (0 bytes):** 22 models (customer, lead, pipeline, product, quotation, invoice, payment, email, whatsapp, task, meeting, document, knowledge_base, workflow, notification, audit_log, api_key, storage, subscription, usage, report, organization_settings) and 12 schema files (excluding the normally-empty `__init__.py`).

---

## 3. Deep Dive: The Flaws

### 3.1 🔴 CRITICAL — Authentication architecture conflict

Two incompatible auth models exist in the same codebase:

- **Backend (current implementation):** `users` table is expected to have `email`, `password_hash`, and `id UUID default uuid4()`. Backend issues its own JWT via `create_access_token()` using `JWT_SECRET_KEY`. `auth_service.login_user` queries `User.email`/`password_hash`.
- **Supabase schema (migrations/0003):** `users.id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE`, and there is **no `email` and no `password_hash` column**. Auth is delegated to Supabase Auth (`auth.users`).

These cannot both be true. Consequences:
- If the Supabase schema is applied, the backend `User` model raises `ProgrammingError` (column `email` / `password_hash` does not exist).
- If the backend schema is used, all the RLS policies (which reference `auth.uid()` and self‑join on `users.organization_id`) are meaningless, and the frontend Supabase client has no auth session.

**Decision required (see §4):** *Option A — Supabase Auth as the single source of truth* (recommended): drop backend password hashing, make `users.id` reference `auth.users(id)`, verify Supabase JWTs in a FastAPI dependency. *Option B — Self‑contained backend auth*: alter migration 0003 to add `email`/`password_hash` and keep backend‑issued JWTs, treating Supabase only as Postgres. Either is viable; mixing both is fatal.

### 3.2 🔴 CRITICAL — Environment cannot run

`backend/venv/` contains only pip 22.3 + setuptools. `venv/Scripts/python -c "from app.main import app"` → `ModuleNotFoundError: No module named 'fastapi'`. Nothing has been installed from `requirements.txt`.

Additionally `requirements.txt` is broken as written:
- `from jose import jwt` in `jwt.py` → needs **`python-jose`** (currently has `pyjwt`, which is a different, unused library).
- `EmailStr` in `schemas/user.py` → needs **`email-validator`**.
- `database.py` uses **sync** `create_engine("postgresql://...")` → needs **`psycopg2-binary`** (currently has only `asyncpg`, unused).
- `passlib[bcrypt]` on Python 3.11 → pin **`bcrypt<4.1`** to avoid the known passlib 1.7.4 incompatibility.
- No version pins anywhere → reproducibility risk.

### 3.3 🔴 CRITICAL — Backend model ↔ DB schema drift

Even the implemented models don't match the Supabase migrations:
- `User` model: `email`, `password_hash`, `uuid4` id → migration: no email/password_hash, id = `auth.users(id)`. ❌
- `ai_memory.py` file contains a **copy‑pasted `AIMessage` class** (`__tablename__ = "ai_messages"`) — the real `ai_memory` table is never modeled. ❌
- `AIMessage` model (in `ai_message.py`) has no `ForeignKey` on `conversation_id`. ⚠️
- `AIConversation` uses `server_default="gen_random_uuid()"` (requires pgcrypto — present in migration 0001, fine if Supabase runs it). ⚠️
- No `Base.metadata.create_all` and no Alembic — the app never creates or validates tables. ❌

### 3.4 🟠 HIGH — Router registration incomplete

`api/v1/router.py` imports and registers only `organizations`, `users`, `auth`. The fully written `health` router is commented out in the header block. 24 other route modules exist as empty stubs. The `root` endpoint and `/docs` work, but the product surface is ~6 endpoints.

### 3.5 🟠 HIGH — Config gaps

`Settings` (config.py) is missing `JWT_ALGORITHM` and `ACCESS_TOKEN_EXPIRE_MINUTES` — both referenced by `jwt.py` → guaranteed `AttributeError` when `create_access_token` runs (i.e., on login). Also `.env` sets `ANTHROPIC_API_KEY` / `GOOGLE_AI_KEY` that `Settings` doesn't declare, while `model_router.py` (future AI routing) will need them.

### 3.6 🟠 HIGH — Security & hygiene defects

- `database.py` prints `settings.DATABASE_URL` (contains credentials) to stdout on every import. Must be removed.
- No CORS middleware → browser calls from `localhost:3000` to `localhost:8000` fail.
- No rate limiting, audit middleware (files are empty stubs), tenant isolation middleware, or global exception handlers.
- `.env` and `.env.local` are gitignored (good) but there is **no `.env.example`** → a fresh clone cannot boot.

### 3.7 🟠 HIGH — Supabase data access blocked

- RLS enabled on only **8 of 63** tables (organizations, users, departments, ai_employees, customers, tasks, documents, storage_files).
- **No `GRANT` statements anywhere** → with `auto_expose_new_tables` unset (defaults to off in newer Supabase), the anon/authenticated roles have **no access to any table**. The frontend's `test/page.tsx` will show data/error failures.
- RLS policies join on `users` → broken until the auth architecture is decided (§3.1).

### 3.8 🟠 HIGH — Frontend is a shell

- `page.tsx` is unmodified `create-next-app` boilerplate.
- No routing beyond `/` and `/test`; no auth pages; no dashboard; no API client for the FastAPI backend; no chat UI for the AI agents.
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` is a non‑standard name (convention: `NEXT_PUBLIC_SUPABASE_ANON_KEY`).

### 3.9 🟡 MEDIUM — Missing operational plumbing

- `workers/celery_app.py` empty → Celery (in requirements) cannot run; no beat/worker config; no background job entrypoints.
- `realtime/` empty → no websocket layer despite a `websockets` dependency.
- `Dockerfile`, `docker-compose.yml`, backend `migrations/` (Alembic), backend `README.md`, `.dockerignore` are 0 bytes.
- `tests/` are 5 empty files; no pytest config.
- No seeding/bootstrap script for first organization + admin user.
- `.env` `DATABASE_URL` is plain `postgresql://` (sync driver assumption) — see §3.2.

### 3.10 🟡 MEDIUM — Repository state

- Git: root‑level Next.js files were deleted (moved into `frontend/`), `backend/`, `frontend/`, `supabase/` all untracked; no meaningful commits. The project restructure is not committed.
- Root `README.md` is still the default create‑next‑app README — zero product documentation.

---

## 4. Proposed Solution — Make It Functional

### 4.1 Architectural decisions (resolve FIRST)

| Decision | Recommendation | Rationale |
|----------|----------------|-----------|
| **Auth model** | **Option A: Supabase Auth as the only auth system.** `users.id` stays a FK to `auth.users(id)`; backend drops passlib/JWT‑issuing and instead *verifies* Supabase JWTs (JWT secret from `SUPABASE_JWT_SECRET`) in a `get_current_user` dependency. | RLS, frontend sessions, and backend all align; it's the industry‑standard pattern for Supabase + FastAPI. Least code. |
| **Schema source of truth** | **Supabase migrations** (already complete) remain canonical. SQLAlchemy models are *mirrors* used for querying; no `create_all`, no Alembic in backend. Add a CI check (`supabase db diff`) later. | Avoids maintaining two schema definitions. |
| **AI provider** | **OpenRouter** as the primary gateway (already configured: `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`) with `model_router.py` fallbacks to Anthropic/Google. | One key = access to many models; matches existing `.env`. |
| **Background jobs** | **Celery + Redis** (already in requirements + `.env` `REDIS_URL`); keep for email/report/embedding workers. `realtime/` uses FastAPI WebSockets. | Standard, matches existing scaffolding. |
| **Frontend ↔ backend** | Frontend authenticates via Supabase; calls FastAPI with the Supabase JWT (Bearer); FastAPI verifies it. Optionally proxy `/api` to `localhost:8000` in `next.config.ts`. | Single token, no duplicate sessions. |

### 4.2 Phased implementation plan

**Phase 0 — Environment boot (½ day)**
1. Fix `requirements.txt`: add `python-jose[cryptography]`, `email-validator`, `psycopg2-binary`, pin `bcrypt<4.1` (until passlib is replaced), pin sensible versions. Remove unused `pyjwt`.
2. `pip install -r requirements.txt` (into `backend/venv`).
3. Fix `config.py`: add `JWT_ALGORITHM="HS256"`, `ACCESS_TOKEN_EXPIRE_MINUTES=60`, `SUPABASE_JWT_SECRET`, `ANTHROPIC_API_KEY`, `GOOGLE_AI_KEY`, `FRONTEND_ORIGINS` (CORS list). Add `.env.example`.
4. Fix `database.py`: remove the `print(settings.DATABASE_URL)` line and duplicate import.
5. **Verify:** `venv/Scripts/python -c "from app.main import app; print(len(app.routes))"` works; `uvicorn app.main:app --reload` serves `/` and `/docs`.

**Phase 1 — Auth reconciliation (1 day)**
1. Decide Option A (§4.1). Create a `dependencies.py` `get_current_user` that decodes Supabase JWT, loads `users` row, returns it.
2. Refactor `auth_service.py` → only *verify* tokens; remove password hashing/issuing. Keep `security.py` only if Option B is chosen.
3. Update `users/routes.py`: register‑via‑webhook pattern (Supabase Auth webhook creates the `users` row) or a `/me` endpoint.
4. Wire `health` router + CORS middleware into `main.py`.
5. **Verify:** register a user in Supabase, hit `/api/v1/auth/me` with the token → 200.

**Phase 2 — Database sanity (½ day)**
1. Start Supabase locally (`supabase start`) → apply all 36 migrations.
2. Add GRANT statements migration (`0037_grants.sql`): grant select/insert/update/delete on all tables to `authenticated`, and necessary grants for `service_role`; enable RLS on remaining 55 tables with tenant policies (reuse the existing policy pattern).
3. Align SQLAlchemy models to the migrations; delete the copy‑paste `AIMessage` from `ai_memory.py` and write the real `AIMemory` model (with `Vector`/`embedding` column via pgvector).
4. **Verify:** `test/page.tsx` shows a successful session + a read of `organizations`.

**Phase 3 — Vertical slice: AI chat MVP (2–3 days)**
1. Implement `ai/model_router.py` (OpenRouter client, model selection by agent role, fallback).
2. Implement `ai/prompts.py` (system prompts per role) and `ai/engine.py` (a `ChatEngine` that takes a prompt + context, calls model_router, returns text).
3. Implement `ai_chat/routes.py` + `ai_conversations` + `ai_messages` routers: create conversation, post message, stream/poll reply, persist to `ai_messages`.
4. Register the new routers in `router.py`.
5. Write the simplest agent (`sales_agent.py`) as a thin wrapper over the engine, then a minimal `orchestrator.py` that routes to one agent.
6. **Verify:** `POST /api/v1/ai/chat` returns an AI reply using OpenRouter.

**Phase 4 — Frontend MVP (2–3 days)**
1. Build auth pages (login with Supabase email/password), a dashboard shell (sidebar with org/agent list), and a chat window that calls the FastAPI `ai/chat` endpoint with the Bearer token.
2. Create a typed API client (`src/lib/api.ts`), standardize `.env.local` key names, and add `next.config.ts` rewrite/proxy for `/api`.
3. Replace boilerplate `page.tsx` with a landing/login redirect.
4. **Verify:** full flow — sign up → org created → chat with Sales agent → reply persisted → visible in UI.

**Phase 5 — Core domain modules (2–3 weeks, priority order)**
1. **CRM/sales/finance/invoicing** (customers, leads, pipeline, products, quotations, invoices, payments) — models, schemas, services, repos, routers, CRUD + RLS.
2. **Tasks, calendar, documents, knowledge base** (needed for agents to act).
3. **AI agents + tools:** implement tools (`crm_tools`, `search_tools`, `email_tools`, etc.) and wire them to agents via the executor; implement `memory.py` (ai_memories with pgvector) and `retriever.py` (RAG over knowledge_base/documents).
4. **Workers:** `celery_app.py` + email/embedding/report workers; Redis running.
5. **Realtime:** websocket notifications for long‑running agent tasks.

**Phase 6 — Production hardening (ongoing)**
1. Global exception handlers, request logging (`core/logging.py`), audit middleware.
2. Rate limiting (Redis), tenant middleware.
3. Tests: replace empty files with pytest suites (unit: engine/model_router; integration: auth, crm, ai_chat). CI hook.
4. Docker: write `Dockerfile` (uvicorn) + `docker-compose.yml` (api, worker, redis, supabase).
5. API keys, billing/usage tracking, webhooks, MFA/SSO — last (business features on top of a stable core).
6. Commit the restructure; write a real README.

### 4.3 Suggested minimum "definition of done" for v0.1

- [ ] `pip install -r requirements.txt` succeeds; `uvicorn` serves `/docs`.
- [ ] Supabase migrations applied; frontend can read its own org data (GRANT + RLS fixed).
- [ ] Login works end‑to‑end (Supabase Auth → FastAPI verifies JWT → `/auth/me`).
- [ ] One AI agent (Sales) answers a chat message via OpenRouter; conversation + messages persisted.
- [ ] Frontend: sign in, see agents, chat with one agent, see history.
- [ ] `pytest` passes a smoke test (`health`, `auth`, `ai_chat`).

---

## 5. Risks & Notes

- **Scope is large.** The schema implies ~20 product domains. Phases 5–6 are multi‑week; Phase 0–4 get you a demoable product.
- **AI cost/latency:** stream responses and persist partial messages; cache embeddings; use cheap models for simple agents.
- **RLS performance:** the `IN (SELECT ... FROM users WHERE id = auth.uid())` pattern is fine at small scale but should become a `tenant_id` claim or security definer helper at scale. It also depends on the `users` table being populated for every `auth.uid()` — which is exactly why Phase 1 (auth reconciliation) must land before RLS can be trusted.
- **Passlib is deprecated/unmaintained** — if Option B is ever needed, migrate to `bcrypt` directly (argon2 also fine).
- The empty test files and duplicate `AIMessage` indicate some generation was cut short mid‑write — treat all 0‑byte files as **not started**, not "done".

---

## 6. Quick Reference: 10 Fastest Wins

1. `pip install -r requirements.txt` after fixing it (jose, email-validator, psycopg2, bcrypt pin).
2. Remove the `print(DATABASE_URL)` in `database.py`. 🔒
3. Add `JWT_ALGORITHM` / `ACCESS_TOKEN_EXPIRE_MINUTES` to `config.py`. 🔥
4. Register `health` router + add CORS in `main.py`.
5. Create `.env.example` from `.env` keys (secrets blanked).
6. Decide Option A auth and write `get_current_user` dependency.
7. Apply Supabase migrations locally; write `0037_grants.sql` + RLS for remaining tables.
8. Delete the bogus `AIMessage` in `ai_memory.py`; write real `AIMemory`.
9. Implement `model_router.py` + `engine.py` + `ai_chat/routes.py` (vertical slice).
10. Build auth + chat in the frontend; wire `/api` proxy.

---

*Generated by an automated deep audit of the repository (file inventory, byte-size analysis, import graph, requirements cross-check, and Supabase schema comparison).*
