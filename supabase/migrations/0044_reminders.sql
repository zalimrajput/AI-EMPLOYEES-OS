-- 0044_reminders.sql
-- AI reminders and follow-ups (targets any entity via type + id).

CREATE TABLE IF NOT EXISTS reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL
        REFERENCES organizations(id)
        ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    target_type TEXT,
    target_id UUID,
    remind_at TIMESTAMPTZ NOT NULL,
    message TEXT,
    channel TEXT DEFAULT 'email',
    triggered BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reminders_org ON reminders(organization_id);
CREATE INDEX IF NOT EXISTS idx_reminders_due ON reminders(remind_at);
CREATE INDEX IF NOT EXISTS idx_reminders_triggered ON reminders(triggered);
