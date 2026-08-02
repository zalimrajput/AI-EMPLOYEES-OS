CREATE TABLE organizations (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name VARCHAR(255) NOT NULL,

    slug VARCHAR(100) UNIQUE NOT NULL,

    industry VARCHAR(100),

    country VARCHAR(100),

    timezone VARCHAR(50)
        DEFAULT 'UTC',

    logo_url TEXT,

    settings JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    updated_at TIMESTAMPTZ DEFAULT NOW()

);