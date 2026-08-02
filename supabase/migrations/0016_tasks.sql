CREATE TABLE tasks (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),


    organization_id UUID
    REFERENCES organizations(id)
    ON DELETE CASCADE,


    assigned_to UUID
    REFERENCES users(id),


    created_by UUID
    REFERENCES users(id),


    title TEXT NOT NULL,


    description TEXT,


    priority TEXT DEFAULT 'medium',


    status TEXT DEFAULT 'todo',


    due_date TIMESTAMPTZ,


    ai_created BOOLEAN DEFAULT FALSE,


    created_at TIMESTAMPTZ DEFAULT NOW()

);