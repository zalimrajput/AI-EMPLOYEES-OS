CREATE TABLE ai_memories (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),


    organization_id UUID
    REFERENCES organizations(id)
    ON DELETE CASCADE,


    employee_id UUID
    REFERENCES ai_employees(id)
    ON DELETE CASCADE,


    content TEXT NOT NULL,


    embedding VECTOR(1536),


    metadata JSONB DEFAULT '{}',


    created_at TIMESTAMPTZ DEFAULT NOW()

);


CREATE INDEX ai_memory_embedding_idx
ON ai_memories
USING ivfflat
(embedding vector_cosine_ops);