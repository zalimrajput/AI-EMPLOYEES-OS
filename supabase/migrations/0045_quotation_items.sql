-- 0045_quotation_items.sql
-- Line items for quotations (supports "25 laptops" style quotations).

CREATE TABLE IF NOT EXISTS quotation_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID
        REFERENCES organizations(id)
        ON DELETE CASCADE,
    quotation_id UUID NOT NULL
        REFERENCES quotations(id)
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

-- Backfill org from the parent quotation
UPDATE quotation_items qi
SET organization_id = q.organization_id
FROM quotations q
WHERE qi.quotation_id = q.id AND qi.organization_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_quotation_items_quotation ON quotation_items(quotation_id);
CREATE INDEX IF NOT EXISTS idx_quotation_items_org ON quotation_items(organization_id);
