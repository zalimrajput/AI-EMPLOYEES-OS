CREATE TABLE email_threads (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL
    REFERENCES organizations(id)
    ON DELETE CASCADE,


    customer_id UUID
    REFERENCES customers(id),


    subject TEXT,


    participants JSONB DEFAULT '{}',


    summary TEXT,


    ai_priority TEXT DEFAULT 'normal',


    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE TABLE emails (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),


    thread_id UUID
    REFERENCES email_threads(id)
    ON DELETE CASCADE,


    sender TEXT,


    receiver TEXT,


    body TEXT,


    direction TEXT,


    ai_generated BOOLEAN DEFAULT FALSE,


    sent_at TIMESTAMPTZ,


    created_at TIMESTAMPTZ DEFAULT NOW()

);