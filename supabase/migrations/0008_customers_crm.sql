CREATE TABLE customers (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),


    organization_id UUID
    REFERENCES organizations(id)
    ON DELETE CASCADE,


    name TEXT NOT NULL,


    email TEXT,


    phone TEXT,


    company TEXT,


    address TEXT,


    notes TEXT,


    created_at TIMESTAMPTZ DEFAULT NOW()

);


CREATE INDEX customers_org_idx
ON customers(organization_id);