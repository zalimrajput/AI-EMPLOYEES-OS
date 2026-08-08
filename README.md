# AI Employee OS

**Status:** Proof of Concept / Scaffold (Not Production Ready)

AI Employee OS is intended to be a multi-tenant SaaS platform that acts as an all-in-one operating system for businesses, augmented with specialized AI agents.

Currently, the project is a **scaffold**. The database schema is fully mature, but the backend AI engine and frontend dashboards are entirely unwritten. 

## Current Architecture State

- **Frontend:** Next.js 16. Scaffolded pages exist (`/dashboard/crm`), but they use hardcoded demo data. Not connected to the backend.
- **Backend:** FastAPI. 95% of the codebase consists of 0-byte stub files. Cannot currently run locally due to dependency conflicts in `requirements.txt`.
- **Database:** PostgreSQL (Supabase). Fully implemented (71 tables) with Row Level Security (RLS) enforcing multi-tenancy.

## Running Locally (Attempting to Run)

The backend is currently broken out of the box. Do not attempt to run it until `requirements.txt` is fixed and the `pyjwt` vs `python-jose` conflict is resolved.

### Database Setup
```bash
cd supabase
supabase start
supabase db push
```

## Documentation
See the generated `CURRENT_STATE.md` and `BACKEND_GAP_ANALYSIS.md` for a precise breakdown of what exists and what is missing.
