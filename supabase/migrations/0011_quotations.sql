CREATE TABLE quotations (

id UUID PRIMARY KEY DEFAULT gen_random_uuid(),


organization_id UUID
REFERENCES organizations(id),


customer_id UUID
REFERENCES customers(id),


quotation_number TEXT,


status TEXT DEFAULT 'draft',


subtotal NUMERIC,


tax NUMERIC,


discount NUMERIC,


total NUMERIC,


pdf_url TEXT,


created_at TIMESTAMPTZ DEFAULT NOW()

);