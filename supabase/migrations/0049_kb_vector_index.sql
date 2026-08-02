-- 0049_kb_vector_index.sql
-- Add the missing vector index on knowledge_articles.embedding so AI Q&A
-- over the knowledge base is fast (documents and ai_memories already have one).

CREATE INDEX IF NOT EXISTS knowledge_articles_embedding_idx
ON knowledge_articles
USING ivfflat
(embedding vector_cosine_ops);
