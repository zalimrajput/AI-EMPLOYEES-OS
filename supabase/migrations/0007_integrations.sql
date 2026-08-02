CREATE TABLE integrations (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),


    organization_id UUID
    REFERENCES organizations(id)
    ON DELETE CASCADE,


    provider TEXT NOT NULL,


    access_token TEXT,


    refresh_token TEXT,


    metadata JSONB DEFAULT '{}',


    connected BOOLEAN DEFAULT TRUE,


    created_at TIMESTAMPTZ DEFAULT NOW()

);