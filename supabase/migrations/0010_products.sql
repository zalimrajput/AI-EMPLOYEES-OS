CREATE TABLE products (

id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

organization_id UUID
REFERENCES organizations(id),


name TEXT,


description TEXT,


price NUMERIC,


tax_rate NUMERIC DEFAULT 0,


created_at TIMESTAMPTZ DEFAULT NOW()

);