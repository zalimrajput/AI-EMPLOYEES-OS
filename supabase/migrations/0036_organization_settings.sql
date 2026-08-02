CREATE TABLE organization_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL UNIQUE
        REFERENCES organizations(id)
        ON DELETE CASCADE,

    company_name VARCHAR(255),

    timezone VARCHAR(100) DEFAULT 'UTC',
    language VARCHAR(20) DEFAULT 'en',
    currency VARCHAR(10) DEFAULT 'USD',

    tax_rate NUMERIC(5,2) DEFAULT 0,

    invoice_prefix VARCHAR(20) DEFAULT 'INV',
    quotation_prefix VARCHAR(20) DEFAULT 'QUO',

    date_format VARCHAR(20) DEFAULT 'YYYY-MM-DD',

    logo_url TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_org_settings_org
ON organization_settings(organization_id);