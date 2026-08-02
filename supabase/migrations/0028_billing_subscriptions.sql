-- 0028_billing_subscriptions.sql


CREATE TABLE IF NOT EXISTS plans (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name TEXT NOT NULL UNIQUE,

    description TEXT,

    price_monthly NUMERIC(10,2) DEFAULT 0,

    price_yearly NUMERIC(10,2) DEFAULT 0,

    max_users INTEGER,

    ai_requests_limit INTEGER,

    storage_limit_gb INTEGER,

    features JSONB DEFAULT '{}'::jsonb,

    active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE TABLE IF NOT EXISTS subscriptions (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL
    REFERENCES organizations(id)
    ON DELETE CASCADE,

    plan_id UUID NOT NULL
    REFERENCES plans(id),

    status TEXT DEFAULT 'active',

    start_date TIMESTAMPTZ DEFAULT NOW(),

    end_date TIMESTAMPTZ,

    trial_end_date TIMESTAMPTZ,

    payment_provider TEXT,

    external_subscription_id TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    updated_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE TABLE IF NOT EXISTS billing_transactions (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL
    REFERENCES organizations(id)
    ON DELETE CASCADE,

    subscription_id UUID
    REFERENCES subscriptions(id)
    ON DELETE SET NULL,

    amount NUMERIC(10,2),

    currency TEXT DEFAULT 'USD',

    payment_status TEXT DEFAULT 'pending',

    payment_provider TEXT,

    transaction_reference TEXT,

    paid_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE INDEX IF NOT EXISTS billing_subscriptions_org_idx
ON subscriptions(organization_id);



CREATE INDEX IF NOT EXISTS billing_transactions_org_idx
ON billing_transactions(organization_id);



-- Default AI Employee OS plans

INSERT INTO plans
(
name,
description,
price_monthly,
max_users,
ai_requests_limit,
storage_limit_gb,
features
)
VALUES

(
'Basic',
'For freelancers and solo entrepreneurs',
19,
1,
500,
1,
'{
"email_assistant":true,
"basic_whatsapp":true,
"basic_crm":true,
"invoices":100,
"quotations":100
}'::jsonb
),


(
'Pro',
'For growing teams',
49,
5,
10000,
20,
'{
"advanced_crm":true,
"whatsapp_automation":true,
"meetings":true,
"calendar":true,
"workflows":true
}'::jsonb
),


(
'Business',
'For enterprises',
149,
NULL,
NULL,
200,
'{
"multiple_ai_employees":true,
"api_access":true,
"erp_integrations":true,
"audit_logs":true,
"sso":true
}'::jsonb
)

ON CONFLICT(name)
DO NOTHING;