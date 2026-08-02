-- 0031_security_mfa_sso.sql


CREATE TABLE IF NOT EXISTS user_sessions (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL
    REFERENCES users(id)
    ON DELETE CASCADE,

    organization_id UUID
    REFERENCES organizations(id)
    ON DELETE CASCADE,

    session_token TEXT NOT NULL,

    ip_address INET,

    user_agent TEXT,

    device_name TEXT,

    last_activity TIMESTAMPTZ DEFAULT NOW(),

    expires_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE TABLE IF NOT EXISTS mfa_settings (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL
    REFERENCES users(id)
    ON DELETE CASCADE,

    method TEXT NOT NULL,

    secret TEXT,

    enabled BOOLEAN DEFAULT FALSE,

    backup_codes JSONB DEFAULT '[]'::jsonb,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id)
);



CREATE TABLE IF NOT EXISTS sso_connections (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL
    REFERENCES organizations(id)
    ON DELETE CASCADE,

    provider TEXT NOT NULL,

    provider_domain TEXT,

    client_id TEXT,

    client_secret TEXT,

    metadata JSONB DEFAULT '{}'::jsonb,

    enabled BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE TABLE IF NOT EXISTS security_events (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID
    REFERENCES organizations(id)
    ON DELETE CASCADE,

    user_id UUID
    REFERENCES users(id)
    ON DELETE SET NULL,

    event_type TEXT NOT NULL,

    ip_address INET,

    metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE INDEX IF NOT EXISTS sessions_user_idx
ON user_sessions(user_id);



CREATE INDEX IF NOT EXISTS security_events_org_idx
ON security_events(organization_id);



CREATE INDEX IF NOT EXISTS sso_connections_org_idx
ON sso_connections(organization_id);