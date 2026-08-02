CREATE TABLE deals (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),


    organization_id UUID
    REFERENCES organizations(id),


    customer_id UUID
    REFERENCES customers(id),


    title TEXT,


    stage TEXT DEFAULT 'lead',


    value NUMERIC DEFAULT 0,


    probability INTEGER DEFAULT 0,


    expected_close DATE,


    created_at TIMESTAMPTZ DEFAULT NOW()

);