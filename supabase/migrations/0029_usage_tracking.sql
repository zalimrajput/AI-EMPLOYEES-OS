-- 0029_usage_tracking.sql


CREATE TABLE IF NOT EXISTS usage_records (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL
    REFERENCES organizations(id)
    ON DELETE CASCADE,


    user_id UUID
    REFERENCES users(id)
    ON DELETE SET NULL,


    ai_employee_id UUID
    REFERENCES ai_employees(id)
    ON DELETE SET NULL,


    usage_type TEXT NOT NULL,


    provider TEXT,


    model TEXT,


    quantity NUMERIC DEFAULT 1,


    tokens_used INTEGER DEFAULT 0,


    metadata JSONB DEFAULT '{}'::jsonb,


    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE TABLE IF NOT EXISTS storage_usage (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),


    organization_id UUID NOT NULL
    REFERENCES organizations(id)
    ON DELETE CASCADE,


    storage_type TEXT,


    file_count INTEGER DEFAULT 0,


    storage_bytes BIGINT DEFAULT 0,


    updated_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE TABLE IF NOT EXISTS api_usage (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),


    organization_id UUID NOT NULL
    REFERENCES organizations(id)
    ON DELETE CASCADE,


    endpoint TEXT,


    request_count INTEGER DEFAULT 1,


    response_status INTEGER,


    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE INDEX IF NOT EXISTS usage_records_org_idx
ON usage_records(organization_id);



CREATE INDEX IF NOT EXISTS usage_records_type_idx
ON usage_records(usage_type);



CREATE INDEX IF NOT EXISTS storage_usage_org_idx
ON storage_usage(organization_id);



CREATE INDEX IF NOT EXISTS api_usage_org_idx
ON api_usage(organization_id);