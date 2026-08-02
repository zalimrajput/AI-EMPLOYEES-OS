CREATE TABLE workflows (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),


    organization_id UUID
    REFERENCES organizations(id),


    name TEXT,


    trigger JSONB,


    actions JSONB,


    active BOOLEAN DEFAULT TRUE,


    created_at TIMESTAMPTZ DEFAULT NOW()

);