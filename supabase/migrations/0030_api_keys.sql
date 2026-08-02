-- 0030_api_keys.sql


CREATE TABLE IF NOT EXISTS api_keys (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),


    organization_id UUID NOT NULL
    REFERENCES organizations(id)
    ON DELETE CASCADE,


    created_by UUID
    REFERENCES users(id)
    ON DELETE SET NULL,


    name TEXT NOT NULL,


    key_hash TEXT NOT NULL,


    last_used_at TIMESTAMPTZ,


    expires_at TIMESTAMPTZ,


    permissions JSONB DEFAULT '{}'::jsonb,


    active BOOLEAN DEFAULT TRUE,


    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE TABLE IF NOT EXISTS webhooks (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),


    organization_id UUID NOT NULL
    REFERENCES organizations(id)
    ON DELETE CASCADE,


    name TEXT NOT NULL,


    url TEXT NOT NULL,


    events JSONB DEFAULT '[]'::jsonb,


    secret TEXT,


    active BOOLEAN DEFAULT TRUE,


    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE TABLE IF NOT EXISTS api_requests (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),


    organization_id UUID NOT NULL
    REFERENCES organizations(id)
    ON DELETE CASCADE,


    api_key_id UUID
    REFERENCES api_keys(id)
    ON DELETE CASCADE,


    endpoint TEXT,


    method TEXT,


    status_code INTEGER,


    response_time_ms INTEGER,


    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE INDEX IF NOT EXISTS api_keys_org_idx
ON api_keys(organization_id);



CREATE INDEX IF NOT EXISTS webhooks_org_idx
ON webhooks(organization_id);



CREATE INDEX IF NOT EXISTS api_requests_org_idx
ON api_requests(organization_id);