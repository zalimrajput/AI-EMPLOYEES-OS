CREATE TABLE audit_logs (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),


    organization_id UUID
    REFERENCES organizations(id),


    user_id UUID
    REFERENCES users(id),


    action TEXT,


    entity TEXT,


    metadata JSONB,


    created_at TIMESTAMPTZ DEFAULT NOW()

);