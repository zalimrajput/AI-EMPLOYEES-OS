CREATE TABLE knowledge_articles (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),


    organization_id UUID
    REFERENCES organizations(id),


    title TEXT,


    content TEXT,


    embedding VECTOR(1536),


    source TEXT,


    created_at TIMESTAMPTZ DEFAULT NOW()

);