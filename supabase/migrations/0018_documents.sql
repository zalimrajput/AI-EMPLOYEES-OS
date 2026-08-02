CREATE TABLE documents (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),


    organization_id UUID
    REFERENCES organizations(id)
    ON DELETE CASCADE,


    uploaded_by UUID
    REFERENCES users(id),


    filename TEXT,


    file_url TEXT,


    mime_type TEXT,


    size BIGINT,


    extracted_text TEXT,


    embedding VECTOR(1536),


    metadata JSONB DEFAULT '{}',


    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE INDEX documents_embedding_idx

ON documents

USING ivfflat
(embedding vector_cosine_ops);