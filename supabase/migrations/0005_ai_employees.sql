CREATE TABLE ai_employees (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL
    REFERENCES organizations(id)
    ON DELETE CASCADE,


    name TEXT NOT NULL,


    role TEXT NOT NULL,


    description TEXT,


    model TEXT DEFAULT 'gpt-5',


    system_prompt TEXT,


    tools JSONB DEFAULT '{}',


    permissions JSONB DEFAULT '{}',


    active BOOLEAN DEFAULT TRUE,


    created_at TIMESTAMPTZ DEFAULT NOW()

);