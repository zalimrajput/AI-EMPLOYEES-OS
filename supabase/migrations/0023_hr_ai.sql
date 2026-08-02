CREATE TABLE employees (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL
    REFERENCES organizations(id)
    ON DELETE CASCADE,

    user_id UUID
    REFERENCES users(id)
    ON DELETE SET NULL,

    employee_code TEXT,

    first_name TEXT NOT NULL,

    last_name TEXT,

    email TEXT,

    phone TEXT,

    department_id UUID
    REFERENCES departments(id),

    position TEXT,

    joining_date DATE,

    salary NUMERIC,


    status TEXT DEFAULT 'active',


    metadata JSONB DEFAULT '{}'::jsonb,


    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE TABLE attendance (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    employee_id UUID
    REFERENCES employees(id)
    ON DELETE CASCADE,

    check_in TIMESTAMPTZ,

    check_out TIMESTAMPTZ,

    status TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE TABLE leave_requests (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    employee_id UUID
    REFERENCES employees(id)
    ON DELETE CASCADE,

    leave_type TEXT,

    start_date DATE,

    end_date DATE,

    reason TEXT,

    status TEXT DEFAULT 'pending',

    approved_by UUID
    REFERENCES users(id),

    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE TABLE job_candidates (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID
    REFERENCES organizations(id)
    ON DELETE CASCADE,

    name TEXT,

    email TEXT,

    phone TEXT,

    resume_url TEXT,

    skills JSONB DEFAULT '[]'::jsonb,

    ai_score NUMERIC,

    status TEXT DEFAULT 'new',

    created_at TIMESTAMPTZ DEFAULT NOW()

);