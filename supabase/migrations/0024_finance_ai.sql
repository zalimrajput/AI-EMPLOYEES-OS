CREATE TABLE expense_categories (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL
    REFERENCES organizations(id)
    ON DELETE CASCADE,

    name TEXT NOT NULL,

    description TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE TABLE expenses (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL
    REFERENCES organizations(id)
    ON DELETE CASCADE,


    category_id UUID
    REFERENCES expense_categories(id)
    ON DELETE SET NULL,


    submitted_by UUID
    REFERENCES users(id),


    title TEXT NOT NULL,


    description TEXT,


    amount NUMERIC(12,2) NOT NULL,


    currency TEXT DEFAULT 'USD',


    expense_date DATE,


    receipt_url TEXT,


    status TEXT DEFAULT 'pending',


    approved_by UUID
    REFERENCES users(id),


    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE TABLE budgets (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID
    REFERENCES organizations(id)
    ON DELETE CASCADE,


    name TEXT,


    amount NUMERIC(12,2),


    period TEXT,


    start_date DATE,


    end_date DATE,


    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE TABLE financial_reports (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),


    organization_id UUID
    REFERENCES organizations(id)
    ON DELETE CASCADE,


    report_type TEXT,


    data JSONB DEFAULT '{}'::jsonb,


    ai_summary TEXT,


    generated_by UUID
    REFERENCES ai_employees(id),


    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE INDEX expenses_org_idx
ON expenses(organization_id);


CREATE INDEX reports_org_idx
ON financial_reports(organization_id);