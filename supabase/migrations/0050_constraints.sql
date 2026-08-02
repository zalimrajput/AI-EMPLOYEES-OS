-- 0050_constraints.sql
-- Consistency hardening: updated_at on mutating tables and CHECK constraints.

-- updated_at for key mutating tables (already present on many)
ALTER TABLE email_threads ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE emails ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE whatsapp_contacts ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE whatsapp_messages ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE documents ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE knowledge_articles ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE workflows ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE integrations ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE ai_employees ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE ai_memories ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE ai_messages ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE usage_records ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Money/quantity CHECK constraints (prevent negative values)
ALTER TABLE deals ADD CONSTRAINT deals_value_nonneg CHECK (value >= 0);
ALTER TABLE products ADD CONSTRAINT products_price_nonneg CHECK (price >= 0);
ALTER TABLE quotations ADD CONSTRAINT quotations_total_nonneg CHECK (total >= 0);
ALTER TABLE invoices ADD CONSTRAINT invoices_amount_nonneg CHECK (amount >= 0);
ALTER TABLE payments ADD CONSTRAINT payments_amount_nonneg CHECK (amount >= 0);
ALTER TABLE quotation_items ADD CONSTRAINT quotation_items_qty_nonneg CHECK (quantity >= 0);
ALTER TABLE quotation_items ADD CONSTRAINT quotation_items_total_nonneg CHECK (line_total >= 0);
ALTER TABLE invoice_items ADD CONSTRAINT invoice_items_qty_nonneg CHECK (quantity >= 0);
ALTER TABLE invoice_items ADD CONSTRAINT invoice_items_total_nonneg CHECK (line_total >= 0);
ALTER TABLE inventory_items ADD CONSTRAINT inventory_qty_nonneg CHECK (quantity >= 0);
ALTER TABLE stock_movements ADD CONSTRAINT stock_movement_qty_nonneg CHECK (quantity >= 0);
