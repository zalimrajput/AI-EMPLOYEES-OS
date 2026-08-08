# AI-EMPLOYEES-OS Audit Report

Diagnostic pass only — no code was modified. Evidence recorded below.
Date: 2026-08-05
Environment: Windows, Python 3.13.5, Node v22.23.1 / npm 10.9.8
Severity scale: **BLOCKER** = prevents boot/running · **AI-BLOCKER** = blocks the AI layer · **COSMETIC** = technical debt.

| Severity | Count | Findings |
|---|---|---|
| BLOCKER | 1 | Frontend `next build` fails (missing `NEXT_PUBLIC_SUPABASE_URL`) — §7 |
| AI-BLOCKER | 0 | — |
| COSMETIC | 7 | dead `app/rag/` package (§5), 4 empty tool files unused (§5), migration 0065 untracked (§2/§3), duplicate pydantic pin (§1), org extra columns not modeled (§3), migration tracking inconsistency (§2), 3 npm high-severity vulns (§7) |

---

## 1. Backend environment

### requirements.txt review
- **fastapi==0.115.6** present (line 2) — OK.
- **psycopg2-binary==2.9.10** present (line 15) — OK, not missing.
- JWT: **python-jose[cryptography]==3.3.0** (line 19). No `pyjwt` anywhere in the repo (`grep pyjwt|import jwt` → 0 hits). No conflict — OK.
- DB driver: **SQLAlchemy==2.0.36** + **psycopg2-binary** (sync). `backend/app/core/database.py:10` uses sync `create_engine` + `sessionmaker`; the codebase is uniformly sync (`_crud.py`, services, routers). No async driver mixed in (no asyncpg anywhere). Consistent — OK.
- Duplicate pin: `pydantic==2.10.4` (line 7) and `pydantic[email]==2.10.4` (line 11) declare the same package twice. **COSMETIC.**
- All other pins (celery, redis, openai, anthropic, google-generativeai, httpx, pgvector, pypdf, pytest) resolved cleanly.

### Fresh virtualenv + pip install
Created `aeo_audit_venv` (Python 3.13.5) and ran `pip install -r requirements.txt`:

```
Successfully installed SQLAlchemy-2.0.36 ... fastapi-0.115.6 ... psycopg2-binary-2.9.10 ...
python-jose-3.3.0 ... openai-1.59.7 anthropic-0.42.0 ... pydantic-2.10.4 ... uvicorn-0.34.0
```

Result: **SUCCESS — zero errors.** (Note: repo ships `__pycache__` compiled for cpython-312; no 3.13 incompatibility observed on install or import.)

### uvicorn boot
`uvicorn app.main:app --reload --port 8123` (from `backend/`):

```
INFO:  Uvicorn running on http://127.0.0.1:8123
INFO:  Application startup complete.
2026-08-05 22:57:12,960 | INFO | app | database connectivity ok
```

Result: **BOOTS.** No traceback. `import app.main` also succeeds standalone (`IMPORT OK`). The app reaches the DB (see §2).

---

## 2. Database connectivity

- **A Supabase/Postgres instance IS reachable** from this environment. `backend/env` configures `DATABASE_URL` pointing at a remote Supabase pooler (`aws-0-ap-southeast-1.pooler.supabase.com:6543`, project `kxddbnybzfwwmjtrosyb`). Verified live:
  - uvicorn startup logged `database connectivity ok`.
  - Direct probe: `SERVER: PostgreSQL 17.6 ...`; `SELECT 1` succeeded.
- Supabase CLI is **not installed** (`supabase` not recognized) and `psql` is not on PATH, so `supabase db diff` could not be run. Migration status was verified directly against `supabase_migrations.schema_migrations`.
- **64 of 65 migrations are recorded; migration `0065_ai_conversations_employee_nullable` is NOT in the tracker.** Despite that, the schema change it makes (`ai_conversations.ai_employee_id` → nullable) IS present in the live DB (verified: `is_nullable=YES`), i.e. it was applied out-of-band without a migration record. **COSMETIC** (schema matches, tracking is inconsistent).
- Applied migrations list (64) and on-disk files (65, `0001`–`0065`) otherwise match 1:1. 78 tables exist in `public`.

---

## 3. Model / schema drift

Compare of `app/models/` against live DB columns and migrations 0034/0035/0053–0058/0065. Full column dumps taken live.

| Table | SQLAlchemy model vs live DB | Verdict |
|---|---|---|
| `ai_conversations` (0034, 0065) | Model: `id, organization_id, user_id, ai_employee_id (nullable), title, status, created_at, updated_at` = live DB exactly (incl. `ai_employee_id` nullable). Migration 0034 has `ai_employee_id NOT NULL`; 0065 drops it. 0065 is on disk and effective in DB but untracked (§2). Model FKs lack `ondelete="CASCADE"` that 0034 declares — no functional impact for ORM use. | OK / COSMETIC |
| `ai_messages` (0035) | Model: `id, organization_id (nullable), conversation_id, role, message, tool_calls, metadata→"metadata", created_at, updated_at`. Live DB matches (incl. `organization_id`, `updated_at` added by migration 0038, applied). `role` model `String` vs DB `VARCHAR(20) CHECK (role IN (...))` — compatible; non-CONSTRAINT role values would be rejected at DB only. | OK / COSMETIC |
| `ai_employees` (0005) | All 13 columns match live DB exactly (names, types, defaults). | OK |
| `users` (0003, 0053–0058) | **No `password_hash` in model or DB** (dropped by 0057 — correct). `email` nullable in both (0055/0057). No unique on email (0058 dropped `users_email_key` — model has none). `organization_id` nullable in both (0055). Model `full_name` nullable, DB `text` nullable — matches trigger (0053/0057). | OK |
| `organizations` (0002, 0056) | `created_by` present in model and DB (0056). DB additionally has `plan, status, max_users, storage_limit_gb, ai_requests_limit` **not modeled**. Harmless for ORM (extra columns ignored on read/write; defaults fill them) but the model lags the DB. | COSMETIC |

No missing columns, no stale columns, no wrong nullability that would break ORM I/O on the audited tables. `password_hash` (the flagged suspect) is cleanly gone.

---

## 4. API router wiring

`backend/app/api/v1/router.py` imports and includes **27 routers**:
organizations, users, auth, modules, departments, ai_chat, ai_conversations, ai_employees, ai_messages, analytics, api_keys, billing, calendar, crm, documents, email, finance, hr, integrations, inventory, knowledge, marketing, organization_settings, sales, storage, tasks, webhooks, whatsapp, workflows, notifications.

- **Every router directory that exists on disk with `routes.py` is registered.** No orphans.
- `health` is the only route package not in `v1/router.py`, but that is **intentional** — `backend/app/main.py:98` imports it and mounts it at `/health`.
- No registered router import-fails: `import app.main` (which pulls in every router) succeeds; the live uvicorn boot confirms all route modules load.

---

## 5. AI layer integrity

### 5.1 Module import sweep (all files under `app/ai`, `app/ai/agents`, `app/ai/tools`)
Imported all 37 `.py` modules individually in a clean interpreter:

```
37 modules imported, 0 failures
OK app.ai.orchestrator / engine / model_router / executor / retriever / embeddings / memory / guardrails / ...
OK app.ai.agents.{base,sales,support,hr,recruiter,finance,accountant,marketing,legal,inventory,executive}
OK app.ai.tools.{__init__,base,crm_tools,hr_tools,invoice_tools,inventory_tools,knowledge_tools,marketing_tools,task_tools}
OK app.ai.tools.{calendar_tools,email_tools,search_tools,document_tools}
```

No `ImportError`, no circular import, no `NameError`.

### 5.2 `app/rag/` (0-byte files) — suspected hard blocker: **NOT a blocker**
`backend/app/rag/*` (6 files, all 0 bytes) is **dead code — nothing imports it**:
`grep "from app.rag|import rag|app.rag."` across the entire backend → **0 matches**.

- `app/ai/retriever.py` and `app/ai/embeddings.py` do **not** import anything from `app/rag/`. `retriever.py:1-159` uses `sqlalchemy.text` pgvector queries plus a keyword fallback; `embeddings.py:12-33` uses the OpenAI client.
- The RAG pipeline is reimplemented in `app/services/document_service.py` (`chunk_text`, `ingest_document`) and `workers/embedding_worker.py` (uses `chunk_text` + `app.ai.embeddings.embed`) — both fully present.
- **Functions "expected but missing" from `app/rag`: NONE are referenced anywhere.** Severity: **COSMETIC** (remove or implement the dead package; nothing breaks).

### 5.3 Tool registry vs the 4 empty tool files — no crash
`app/ai/tools/__init__.py:4-11` imports **only** the 7 implemented groups: `CRM_TOOLS, HR_TOOLS, INVOICE_TOOLS, INVENTORY_TOOLS, KNOWLEDGE_TOOLS, MARKETING_TOOLS, TASK_TOOLS`. It does **not** import `email_tools`, `search_tools`, `calendar_tools`, or `document_tools`, so the 4 empty files **cannot crash import time**. They are unused placeholders. Severity: **COSMETIC.**

Cross-check: every tool name referenced by every agent's `allowed_tools` (11 agents incl. `DEFAULT_AGENT`) resolves to a registered tool (e.g. `search_crm`, `get_customer`, `get_document`, `create_meeting`, `create_email_draft`, `list_candidates`, `list_inventory`, …). No agent points at a tool that only an empty file would have provided — no runtime "Unknown tool" risk from configuration.

### 5.4 Call path for `POST /api/v1/ai-chat/messages` — all links exist, signatures match
1. `app/api/v1/ai_chat/routes.py:167` `send_message(...)` → `execute_turn(db, me.organization_id, str(me.id), conversation, text, employee=..., history_messages=...)`
2. `app/ai/orchestrator.py:40` `execute_turn(db, organization_id, user_id, conversation, user_message, employee, history_messages, model, temperature)` — positional/keyword call matches. Line 67 calls:
3. `app/ai/engine.py:95` `run_agent(db, *, organization_id, user_id, agent, user_message, memory, context, model, temperature)` — all kwargs passed at orchestrator.py:67-77 exist. Line 126 calls:
4. `app/ai/model_router.py:125` `complete_with_tools(messages, tools, model, temperature, tool_choice, max_tokens)` — exists, kwargs match. Tool execution at engine.py:179 calls:
5. `app/ai/executor.py:14` `run(db, tool_name, organization_id, user_id, arguments, allowed_tools)` — exists, matches. It delegates to `app.ai.tools.execute_tool` (tools/`__init__.py:30`).

No phantom function names on the whole path.

### 5.5 Provider-key handling — graceful, no server crash
- `OPENROUTER_API_KEY` is declared in `app/core/config.py:36` and documented in `backend/.env.example:34` (both present). Other providers (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_AI_KEY`) likewise in config.py:42-44.
- A real `OPENROUTER_API_KEY` (plus Anthropic/Google keys) is set in `backend/env` — not printed here.
- **Missing-key behavior** (verified by reading the code path, not by external calls):
  - `model_router.complete_with_tools` / `complete` / `stream` raise `ModelRouterError("... is not configured")` when a provider key is absent (`model_router.py:53-54, 91, 102, 118, 154, 158, 174`).
  - `engine.run_agent` catches it (`engine.py:135-147`): for native tool-calling it retries once via the envelope fallback (`native=False`), and on the second failure logs and returns a polite string — `"Sorry, the language model is temporarily unavailable (...). Please try again in a moment."` It **never re-raises** and never crashes the request.
  - The SSE stream endpoint also wraps the router call in try/except and emits `[stream error: ...]` (`routes.py:235-236`).
- **Conclusion: the AI layer fails gracefully without keys; it does not take the server down.** No AI-BLOCKER found in the AI layer.

---

## 6. Existing tests

`backend/tests/` contains: `conftest.py`, `test_agents.py`, `test_ai_engine.py`, `test_auth.py`, `test_crm.py`, `test_documents.py`.

Ran `pytest tests -v` (live DB reachable, so DB-marked tests were NOT skipped):

```
collected 36 items
test_agents.py .....               [ 13%]
test_ai_engine.py ................. [ 61%]
test_auth.py ....                  [ 72%]
test_crm.py ...                    [ 80%]
test_documents.py .......          [100%]
=================== 36 passed, 2 warnings in 8.80s ===================
```

- **36 passed, 0 failed, 0 errors.**
- 2 warnings: `DeprecationWarning: datetime.datetime.utcnow()` from `python-jose` (`jose/jwt.py:311`) — **COSMETIC.**

---

## 7. Frontend sanity

### npm install
`npm install` → **success**: `added 432 packages, audited 433`. **3 high-severity vulnerabilities** reported (`npm audit fix --force` suggested) — **COSMETIC** but should be reviewed.

### npm run build — **BLOCKER**
```
▲ Next.js 16.2.12 (Turbopack)
✓ Compiled successfully in 13.1s
Running TypeScript ... Finished TypeScript in 9.6s
Error occurred prerendering page "/dashboard/analytics".
Error: supabaseUrl is required.
    at ...frontend\.next\server\chunks\ssr\[turbopack]_runtime.js:853
Export encountered an error on /(app)/dashboard/analytics/page: /dashboard/analytics, exiting the build.
⨯ Next.js build worker exited with code: 1 and signal: null
```

Cause: `frontend/src/lib/supabase/client.ts:3-4` reads `process.env.NEXT_PUBLIC_SUPABASE_URL!` / `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!` and calls `createClient(...)` at module scope (line 6). The values are only present in `frontend/env.download`, which **Next.js does not read** (it reads `.env.local`/`.env`); there is **no `.env` or `.env.local`** in `frontend/`. At prerender time the variables are `undefined`, so `createClient(undefined, undefined)` throws `supabaseUrl is required.` — the `/dashboard/analytics` page instantiates the Supabase client during static generation, failing the build.
Remediation (not applied): copy `env.download` → `.env.local`.

### frontend/src/services/business.ts — NOT 100% mock
`business.ts` is wired to the real backend:
- Imports `api` from `@/lib/api/client` (line 1) and calls real endpoints: `api.fetchCustomers()`, `api.fetchLeads()`, `api.fetchQuotations()`, `api.fetchInvoices()`, `api.fetchMeetings()`, plus `create*` mutations (lines 41-108).
- Demo data (`DEMO_CUSTOMERS`, `DEMO_LEADS`, …) is only a **fallback**: `withDemo()` returns demo rows only when the API returns an empty list, and returns `{source:"error"}` on API failure (lines 29-38).
- `frontend/src/lib/api/client.ts` targets the FastAPI backend at `NEXT_PUBLIC_BACKEND_URL` (default `http://localhost:8000`) with a Supabase bearer token.
- **COSMETIC note:** the demo/`db` fallback is deliberate and documented, not leftover mock scaffolding.

---

## Summary of open items

1. **BLOCKER — Frontend build**: missing `frontend/.env.local`; `NEXT_PUBLIC_SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` undefined → `supabaseUrl is required` on prerender of `/dashboard/analytics`.
2. **COSMETIC — Migration tracking**: `0065_ai_conversations_employee_nullable` applied to the DB but not recorded in `supabase_migrations.schema_migrations` (64 recorded vs 65 on disk).
3. **COSMETIC — Dead `app/rag/`**: all 6 files 0-byte and unreferenced; not a blocker.
4. **COSMETIC — Empty tool files**: `email_tools/search_tools/calendar_tools/document_tools` are 0-byte and unregistered; harmless.
5. **COSMETIC — `organizations` extra columns** (`plan`, `status`, `max_users`, `storage_limit_gb`, `ai_requests_limit`) not modeled.
6. **COSMETIC — requirements.txt**: duplicate `pydantic`/`pydantic[email]` pins.
7. **COSMETIC — frontend**: 3 high-severity npm vulnerabilities; python-jose `utcnow()` deprecation warning in tests.

**No AI-BLOCKERs found.** The AI layer imports cleanly, the tool registry is safe, the `app/rag` empty package is unreferenced, the `/ai-chat/messages` call path is fully wired with matching signatures, and missing LLM keys fail gracefully.
