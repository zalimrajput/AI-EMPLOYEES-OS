-- 0033_rls_policies.sql
-- Multi Tenant Security


ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;


ALTER TABLE users ENABLE ROW LEVEL SECURITY;


ALTER TABLE departments ENABLE ROW LEVEL SECURITY;


ALTER TABLE ai_employees ENABLE ROW LEVEL SECURITY;


ALTER TABLE customers ENABLE ROW LEVEL SECURITY;


ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;


ALTER TABLE documents ENABLE ROW LEVEL SECURITY;


ALTER TABLE storage_files ENABLE ROW LEVEL SECURITY;



CREATE POLICY organizations_isolation
ON organizations
FOR ALL
USING (
    id IN (
        SELECT organization_id
        FROM users
        WHERE id = auth.uid()
    )
);



CREATE POLICY users_isolation
ON users
FOR ALL
USING (
    organization_id IN (
        SELECT organization_id
        FROM users
        WHERE id = auth.uid()
    )
);



CREATE POLICY departments_isolation
ON departments
FOR ALL
USING (
    organization_id IN (
        SELECT organization_id
        FROM users
        WHERE id = auth.uid()
    )
);



CREATE POLICY ai_employee_isolation
ON ai_employees
FOR ALL
USING (
    organization_id IN (
        SELECT organization_id
        FROM users
        WHERE id = auth.uid()
    )
);



CREATE POLICY customers_isolation
ON customers
FOR ALL
USING (
    organization_id IN (
        SELECT organization_id
        FROM users
        WHERE id = auth.uid()
    )
);



CREATE POLICY tasks_isolation
ON tasks
FOR ALL
USING (
    organization_id IN (
        SELECT organization_id
        FROM users
        WHERE id = auth.uid()
    )
);



CREATE POLICY documents_isolation
ON documents
FOR ALL
USING (
    organization_id IN (
        SELECT organization_id
        FROM users
        WHERE id = auth.uid()
    )
);



CREATE POLICY storage_files_isolation
ON storage_files
FOR ALL
USING (
    organization_id IN (
        SELECT organization_id
        FROM users
        WHERE id = auth.uid()
    )
);