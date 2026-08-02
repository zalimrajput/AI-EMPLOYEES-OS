-- 0047_invoice_extensions.sql
-- Invoice extras from the product spec: recurring invoices, QR codes,
-- payment links, AI summaries; also standardize money to NUMERIC(12,2).

ALTER TABLE invoices ADD COLUMN IF NOT EXISTS recurrence_interval INTEGER;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS recurrence_period TEXT;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS next_billing_date DATE;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS payment_link_url TEXT;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS qr_code_url TEXT;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS ai_summary TEXT;

ALTER TABLE customers ADD COLUMN IF NOT EXISTS ai_summary TEXT;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active';
ALTER TABLE customers ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Standardize money columns to NUMERIC(12,2)
ALTER TABLE deals ALTER COLUMN value TYPE NUMERIC(12,2);
ALTER TABLE products ALTER COLUMN price TYPE NUMERIC(12,2);
ALTER TABLE quotations ALTER COLUMN subtotal TYPE NUMERIC(12,2);
ALTER TABLE quotations ALTER COLUMN tax TYPE NUMERIC(12,2);
ALTER TABLE quotations ALTER COLUMN discount TYPE NUMERIC(12,2);
ALTER TABLE quotations ALTER COLUMN total TYPE NUMERIC(12,2);
ALTER TABLE invoices ALTER COLUMN amount TYPE NUMERIC(12,2);
ALTER TABLE payments ALTER COLUMN amount TYPE NUMERIC(12,2);
