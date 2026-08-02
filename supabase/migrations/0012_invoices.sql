CREATE TABLE invoices (

id UUID PRIMARY KEY DEFAULT gen_random_uuid(),


organization_id UUID
REFERENCES organizations(id),


customer_id UUID
REFERENCES customers(id),


invoice_number TEXT,


amount NUMERIC,


status TEXT DEFAULT 'unpaid',


due_date DATE,


pdf_url TEXT,


created_at TIMESTAMPTZ DEFAULT NOW()

);