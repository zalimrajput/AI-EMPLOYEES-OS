CREATE TABLE meetings (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),


    organization_id UUID
    REFERENCES organizations(id),


    title TEXT,


    start_time TIMESTAMPTZ,


    end_time TIMESTAMPTZ,


    participants JSONB,


    transcript TEXT,


    summary TEXT,


    action_items JSONB,


    created_at TIMESTAMPTZ DEFAULT NOW()

);