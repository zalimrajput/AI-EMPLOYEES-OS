CREATE TABLE payments (

id UUID PRIMARY KEY DEFAULT gen_random_uuid(),


invoice_id UUID
REFERENCES invoices(id),


amount NUMERIC,


payment_method TEXT,


paid_at TIMESTAMPTZ DEFAULT NOW()

);