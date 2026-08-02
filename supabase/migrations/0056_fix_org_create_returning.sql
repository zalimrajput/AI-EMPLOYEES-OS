-- 0056_fix_org_create_returning.sql
-- Bug: POST /rest/v1/organizations with `Prefer: return=representation`
-- (supabase-js `.insert().select()`) failed with 403 "new row violates
-- row-level security policy for table organizations".
--
-- Root cause (verified empirically on the live DB):
--   `INSERT ... RETURNING` output is filtered by the SELECT policy
--   `id = current_org_id()`. `current_org_id()` reads `users.organization_id`
--   using the *statement snapshot*, which is taken before the
--   `trg_set_org_creator` AFTER INSERT trigger runs. The creator's membership
--   therefore never exists in the snapshot used by the RETURNING check, so the
--   row is filtered out and PostgreSQL raises the RLS error. A bare INSERT
--   (no RETURNING) has no such check, which is why it returned 201.
--
-- Fix: track the creator on the org row itself (`created_by uuid
-- DEFAULT auth.uid()`) and include `created_by = auth.uid()` in the tenant
-- policy. The policy is then evaluated against the NEW row being returned
-- (same statement, no cross-table snapshot read), so the RETURNING row is
-- visible and `.insert().select()` works. The AFTER INSERT trigger still
-- assigns `users.organization_id`, which subsequent statements read normally.
--
-- Note: a BEFORE INSERT trigger + nested UPDATE was considered and rejected —
-- it raises a ForeignKeyViolation (`users.organization_id` -> organizations)
-- because the org row does not exist yet when the nested UPDATE's FK check
-- runs, and it would still not fix the statement-snapshot visibility problem.

ALTER TABLE public.organizations
    ADD COLUMN IF NOT EXISTS created_by uuid DEFAULT auth.uid();

DROP POLICY IF EXISTS organizations_tenant_isolation ON public.organizations;
CREATE POLICY organizations_tenant_isolation ON public.organizations
    FOR ALL
    TO authenticated
    USING (id = public.current_org_id() OR created_by = auth.uid());

-- The FOR ALL policy above (WITH CHECK inherits USING) makes INSERT pass even
-- without organizations_create, but that policy is kept: it is harmless and
-- preserves the explicit, self-documenting "any authenticated user may create
-- an org" intent. The AFTER trigger trg_set_org_creator (0053) is unchanged.
