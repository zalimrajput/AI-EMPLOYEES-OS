CREATE TABLE departments (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL
    REFERENCES organizations(id)
    ON DELETE CASCADE,

    name TEXT NOT NULL,

    description TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()

);