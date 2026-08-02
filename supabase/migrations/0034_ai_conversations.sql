CREATE TABLE ai_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ai_employee_id UUID NOT NULL REFERENCES ai_employees(id) ON DELETE CASCADE,

    title VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ai_conversations_org
ON ai_conversations(organization_id);

CREATE INDEX idx_ai_conversations_user
ON ai_conversations(user_id);

CREATE INDEX idx_ai_conversations_employee
ON ai_conversations(ai_employee_id);