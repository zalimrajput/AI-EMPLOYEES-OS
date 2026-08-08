# Development Rules

These rules must be strictly adhered to by all developers contributing to AI Employee OS.

## 1. Coding Standards
- **Python (Backend):** Follow PEP 8 guidelines. Use `black` for formatting and `flake8` for linting. All functions and methods must have type hints.
- **TypeScript (Frontend):** Strict mode must be enabled. Avoid `any`; use explicit interfaces. Use Prettier for formatting and ESLint for linting.

## 2. Folder Conventions
- **Backend:**
  - `app/api/v1/`: Contains all route definitions, grouped by feature (e.g., `crm/`, `users/`).
  - `app/services/`: Contains all core business logic. Routers should not contain complex logic.
  - `app/ai/`: Contains AI-specific code (agents, tools, memory, engine).
- **Frontend:**
  - `src/components/ui/`: Reusable, generic UI components (Buttons, Inputs).
  - `src/app/(app)/dashboard/`: Layouts and pages for the authenticated dashboard.

## 3. Naming Conventions
- **Database Tables:** `snake_case`, plural (`users`, `ai_employees`).
- **Database Columns:** `snake_case` (`first_name`, `organization_id`).
- **Python Variables/Functions:** `snake_case`.
- **Python Classes:** `PascalCase`.
- **TypeScript Components:** `PascalCase` (`ChatInterface`).
- **TypeScript Files:** `kebab-case.tsx` (`chat-interface.tsx`).

## 4. Git Workflow
- **Branching:** Use `feature/<feature-name>`, `bugfix/<bug-name>`, or `hotfix/<issue>`.
- **Commits:** Follow Conventional Commits format (`feat: ...`, `fix: ...`, `docs: ...`).
- **Merging:** PRs must be reviewed by at least one other developer. Squash and merge into `main`.

## 5. API Rules
- All endpoints must be versioned (`/api/v1/...`).
- Endpoints must return consistent JSON structures.
- Use standard HTTP status codes (200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 500 Internal Error).
- All endpoints, except webhooks or public integrations, must require a valid Supabase JWT.

## 6. Database Rules
- **No Direct Schema Changes via ORM:** SQLAlchemy's `Base.metadata.create_all()` is strictly forbidden. All schema changes must be done via Supabase SQL migrations.
- **Row Level Security (RLS):** Every new table containing tenant data MUST include an `organization_id` column and an associated RLS policy ensuring users can only read/write their own organization's data.

## 7. Security Rules
- **Passwords:** Never store passwords in the `public` Postgres schema. All authentication credentials belong exclusively in `auth.users` managed by Supabase.
- **Secrets:** Never log sensitive information (API keys, connection strings, JWTs). Ensure `database.py` and `config.py` do not `print()` variables.

## 8. Testing Rules
- Unit tests must be written for all core AI Engine logic and business services.
- Integration tests must be written for critical API endpoints (Auth, AI Chat).
- Code cannot be merged if tests fail or if test coverage drops below established thresholds.

## 9. Documentation Rules
- All new features must be documented in the `README.md` or a feature-specific markdown file.
- Any changes to the database schema must be documented by updating the Mermaid ER diagrams in the documentation.
- Python code should utilize docstrings for classes and complex functions.

## 10. Review Checklist
Before requesting a review, ensure:
- [ ] Code compiles/runs locally without errors.
- [ ] No secrets are hardcoded or printed.
- [ ] RLS policies are applied to any new tables.
- [ ] TypeScript types are strict (no `any`).
- [ ] Python type hints are complete.
- [ ] Tests have been added/updated and pass.
