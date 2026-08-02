CREATE TABLE marketing_campaigns (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL
    REFERENCES organizations(id)
    ON DELETE CASCADE,

    name TEXT NOT NULL,

    description TEXT,

    campaign_type TEXT,

    status TEXT DEFAULT 'draft',

    start_date DATE,

    end_date DATE,

    budget NUMERIC(12,2),

    created_by UUID
    REFERENCES users(id),

    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE TABLE audience_segments (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL
    REFERENCES organizations(id)
    ON DELETE CASCADE,

    name TEXT NOT NULL,

    rules JSONB DEFAULT '{}'::jsonb,

    customer_count INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE TABLE marketing_content (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL
    REFERENCES organizations(id)
    ON DELETE CASCADE,

    campaign_id UUID
    REFERENCES marketing_campaigns(id)
    ON DELETE CASCADE,

    content_type TEXT,

    title TEXT,

    content TEXT,

    ai_generated BOOLEAN DEFAULT FALSE,

    approved BOOLEAN DEFAULT FALSE,

    metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE TABLE email_campaigns (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID
    REFERENCES organizations(id)
    ON DELETE CASCADE,

    campaign_id UUID
    REFERENCES marketing_campaigns(id)
    ON DELETE CASCADE,

    subject TEXT,

    template TEXT,

    sent_count INTEGER DEFAULT 0,

    opened_count INTEGER DEFAULT 0,

    clicked_count INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE INDEX marketing_campaign_org_idx
ON marketing_campaigns(organization_id);


CREATE INDEX marketing_content_campaign_idx
ON marketing_content(campaign_id);