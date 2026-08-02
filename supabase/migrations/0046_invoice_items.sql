-- 0046_invoice_items.sql
-- Line items for invoices.

CREATE TABLE IF NOT EXISTS invoice_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID
        REFERENCES organizations(id)
        ON DELETE CASCADE,
    invoice_id UUID NOT NULL
        REFERENCES invoices(id)
        ON DELETE CASCADE,
    product_id UUID REFERENCES products(id) ON DELETE SET NULL,
    description TEXT,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price NUMERIC(12,2) NOT NULL DEFAULT 0,
    tax_rate NUMERIC(5,2) DEFAULT 0,
    discount NUMERIC(12,2) DEFAULT 0,
    line_total NUMERIC(12,2) NOT NULL DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Backfill org from the parent invoice
UPDATE invoice_items ii
SET organization_id = i.organization_id
FROM invoices i
WHERE ii.invoice_id = i.id AND ii.organization_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice ON invoice_items(invoice_id);
CREATE INDEX IF NOT EXISTS idx_invoice_items_org ON invoice_items(organization_id);
