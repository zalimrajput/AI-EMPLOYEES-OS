CREATE TABLE users (

    id UUID PRIMARY KEY REFERENCES auth.users(id)
    ON DELETE CASCADE,

    organization_id UUID NOT NULL
    REFERENCES organizations(id)
    ON DELETE CASCADE,

    full_name TEXT,

    avatar_url TEXT,

    phone TEXT,

    status TEXT DEFAULT 'active',

    created_at TIMESTAMPTZ DEFAULT NOW(),

    updated_at TIMESTAMPTZ DEFAULT NOW()

);


CREATE INDEX users_org_idx
ON users(organization_id);