-- AI conversations may be started without a specific AI employee
-- (generic assistant chat). Aligns the schema with the API contract
-- (ai_chat/routes.py allows ai_employee_id=None).
ALTER TABLE ai_conversations
    ALTER COLUMN ai_employee_id DROP NOT NULL;
