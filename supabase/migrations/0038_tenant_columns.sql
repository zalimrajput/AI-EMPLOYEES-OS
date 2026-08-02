-- 0038_tenant_columns.sql
-- Add organization_id to child tables that currently resolve tenancy only
-- through parent FKs. This makes RLS policies uniform and fast.

-- payments -> invoice
ALTER TABLE payments ADD COLUMN IF NOT EXISTS organization_id UUID
    REFERENCES organizations(id) ON DELETE CASCADE;

-- emails -> thread
ALTER TABLE emails ADD COLUMN IF NOT EXISTS organization_id UUID
    REFERENCES organizations(id) ON DELETE CASCADE;

-- whatsapp_messages -> contact
ALTER TABLE whatsapp_messages ADD COLUMN IF NOT EXISTS organization_id UUID
    REFERENCES organizations(id) ON DELETE CASCADE;

-- notifications -> user
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS organization_id UUID
    REFERENCES organizations(id) ON DELETE CASCADE;

-- attendance -> employee
ALTER TABLE attendance ADD COLUMN IF NOT EXISTS organization_id UUID
    REFERENCES organizations(id) ON DELETE CASCADE;

-- leave_requests -> employee
ALTER TABLE leave_requests ADD COLUMN IF NOT EXISTS organization_id UUID
    REFERENCES organizations(id) ON DELETE CASCADE;

-- mfa_settings -> user
ALTER TABLE mfa_settings ADD COLUMN IF NOT EXISTS organization_id UUID
    REFERENCES organizations(id) ON DELETE CASCADE;

-- file_access_permissions -> file
ALTER TABLE file_access_permissions ADD COLUMN IF NOT EXISTS organization_id UUID
    REFERENCES organizations(id) ON DELETE CASCADE;

-- ai_messages -> conversation
ALTER TABLE ai_messages ADD COLUMN IF NOT EXISTS organization_id UUID
    REFERENCES organizations(id) ON DELETE CASCADE;

-- Backfill from parent rows (idempotent)
UPDATE payments p
SET organization_id = i.organization_id
FROM invoices i
WHERE p.invoice_id = i.id AND p.organization_id IS NULL;

UPDATE emails e
SET organization_id = t.organization_id
FROM email_threads t
WHERE e.thread_id = t.id AND e.organization_id IS NULL;

UPDATE whatsapp_messages w
SET organization_id = c.organization_id
FROM whatsapp_contacts c
WHERE w.contact_id = c.id AND w.organization_id IS NULL;

UPDATE notifications n
SET organization_id = u.organization_id
FROM users u
WHERE n.user_id = u.id AND n.organization_id IS NULL;

UPDATE attendance a
SET organization_id = e.organization_id
FROM employees e
WHERE a.employee_id = e.id AND a.organization_id IS NULL;

UPDATE leave_requests l
SET organization_id = e.organization_id
FROM employees e
WHERE l.employee_id = e.id AND l.organization_id IS NULL;

UPDATE mfa_settings m
SET organization_id = u.organization_id
FROM users u
WHERE m.user_id = u.id AND m.organization_id IS NULL;

UPDATE file_access_permissions f
SET organization_id = s.organization_id
FROM storage_files s
WHERE f.file_id = s.id AND f.organization_id IS NULL;

UPDATE ai_messages m
SET organization_id = c.organization_id
FROM ai_conversations c
WHERE m.conversation_id = c.id AND m.organization_id IS NULL;
