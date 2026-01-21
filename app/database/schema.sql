-- 1) Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- 2) Collection table (LangChain Postgres PGVector)
CREATE TABLE IF NOT EXISTS langchain_pg_collection (
    name VARCHAR,
    cmetadata JSONB,
    uuid UUID PRIMARY KEY
);

-- 3) Embedding table (IMPORTANT: must have "id" column)
-- LangChain expects: id, collection_id, embedding, document, cmetadata
CREATE TABLE IF NOT EXISTS langchain_pg_embedding (
    id TEXT PRIMARY KEY,  -- <--- this is what your runtime query expects
    collection_id UUID REFERENCES langchain_pg_collection(uuid) ON DELETE CASCADE,
    embedding VECTOR(384),
    document TEXT,
    cmetadata JSONB
);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_pg_embedding_collection_id
ON langchain_pg_embedding(collection_id);

-- Optional: vector index (choose ONE based on your pgvector version/preference)
-- HNSW (great quality/latency)
-- CREATE INDEX IF NOT EXISTS idx_pg_embedding_hnsw
-- ON langchain_pg_embedding USING hnsw (embedding vector_cosine_ops);

-- IVFFLAT (good for large datasets; requires ANALYZE and tuning)
-- CREATE INDEX IF NOT EXISTS idx_pg_embedding_ivfflat
-- ON langchain_pg_embedding USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 4) Chat history
-- IMPORTANT: langchain_postgres.PostgresChatMessageHistory can create this itself.
-- If you want to keep it in schema.sql, align with the documented columns. :contentReference[oaicite:1]{index=1}
CREATE TABLE IF NOT EXISTS chat_history (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL,
    message JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_history(session_id);

-- 5) Research notebook (recommended: use UUID for session_id for consistency)
CREATE TABLE IF NOT EXISTS research_entries (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL,
    query_text TEXT NOT NULL,
    answer_text TEXT NOT NULL,

    epistemic_score FLOAT,
    reasoning_path TEXT,
    citations JSONB,

    verification_status VARCHAR(50) DEFAULT 'pending',
    user_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_research_session ON research_entries(session_id);
CREATE INDEX IF NOT EXISTS idx_verification ON research_entries(verification_status);
