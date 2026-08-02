CREATE TABLE warehouses (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL
    REFERENCES organizations(id)
    ON DELETE CASCADE,

    name TEXT NOT NULL,

    address TEXT,

    manager_id UUID
    REFERENCES users(id),

    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE TABLE suppliers (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL
    REFERENCES organizations(id)
    ON DELETE CASCADE,

    name TEXT NOT NULL,

    email TEXT,

    phone TEXT,

    address TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE TABLE inventory_items (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL
    REFERENCES organizations(id)
    ON DELETE CASCADE,


    product_id UUID
    REFERENCES products(id)
    ON DELETE CASCADE,


    warehouse_id UUID
    REFERENCES warehouses(id)
    ON DELETE CASCADE,


    quantity INTEGER DEFAULT 0,


    minimum_stock INTEGER DEFAULT 0,


    reorder_level INTEGER DEFAULT 0,


    updated_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE TABLE stock_movements (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),


    organization_id UUID
    REFERENCES organizations(id)
    ON DELETE CASCADE,


    inventory_item_id UUID
    REFERENCES inventory_items(id)
    ON DELETE CASCADE,


    movement_type TEXT,


    quantity INTEGER,


    reference_type TEXT,


    reference_id UUID,


    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE TABLE purchase_orders (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),


    organization_id UUID
    REFERENCES organizations(id)
    ON DELETE CASCADE,


    supplier_id UUID
    REFERENCES suppliers(id),


    order_number TEXT,


    status TEXT DEFAULT 'draft',


    total_amount NUMERIC(12,2),


    expected_date DATE,


    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE INDEX inventory_org_idx
ON inventory_items(organization_id);


CREATE INDEX stock_movement_item_idx
ON stock_movements(inventory_item_id);