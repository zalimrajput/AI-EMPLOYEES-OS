-- 0032_storage_management.sql


CREATE TABLE IF NOT EXISTS storage_files (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL
    REFERENCES organizations(id)
    ON DELETE CASCADE,

    uploaded_by UUID
    REFERENCES users(id)
    ON DELETE SET NULL,

    file_name TEXT NOT NULL,

    file_path TEXT NOT NULL,

    bucket TEXT DEFAULT 'documents',

    mime_type TEXT,

    file_size BIGINT DEFAULT 0,

    storage_provider TEXT DEFAULT 'supabase',

    url TEXT,

    entity_type TEXT,

    entity_id UUID,

    metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE TABLE IF NOT EXISTS storage_quotas (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL
    REFERENCES organizations(id)
    ON DELETE CASCADE,

    max_storage_bytes BIGINT DEFAULT 1073741824,

    used_storage_bytes BIGINT DEFAULT 0,

    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(organization_id)

);



CREATE TABLE IF NOT EXISTS file_access_permissions (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    file_id UUID NOT NULL
    REFERENCES storage_files(id)
    ON DELETE CASCADE,

    user_id UUID
    REFERENCES users(id)
    ON DELETE CASCADE,

    permission TEXT DEFAULT 'read',

    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE INDEX IF NOT EXISTS storage_files_org_idx
ON storage_files(organization_id);



CREATE INDEX IF NOT EXISTS storage_files_entity_idx
ON storage_files(entity_type, entity_id);



CREATE INDEX IF NOT EXISTS file_permissions_file_idx
ON file_access_permissions(file_id);