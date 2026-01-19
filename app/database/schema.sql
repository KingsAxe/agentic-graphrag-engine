-- 1. Enable the pgvector extension to work with embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. LangChain standard tables for PGVector (Collection Management)
CREATE TABLE IF NOT EXISTS langchain_pg_collection (
    name VARCHAR,
    cmetadata JSONB,
    uuid UUID PRIMARY KEY
);

-- 3. LangChain standard tables for PGVector (Embedding Storage)
CREATE TABLE IF NOT EXISTS langchain_pg_embedding (
    collection_id UUID REFERENCES langchain_pg_collection(uuid) ON DELETE CASCADE,
    embedding VECTOR(384), -- Adjusted for BGE-Small (384 dimensions). Change to 768 for BGE-Base.
    document TEXT,
    cmetadata JSONB,
    custom_id VARCHAR,
    uuid UUID PRIMARY KEY
);

-- 4. Persistent Chat History (Used by PostgresChatMessageHistory)
CREATE TABLE IF NOT EXISTS chat_history (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    message JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. PHASE 3: The Research Notebook (Crystallized Knowledge)
-- This table stores verified insights that have been audited and approved.
CREATE TABLE IF NOT EXISTS research_entries (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    query_text TEXT NOT NULL,
    answer_text TEXT NOT NULL,
    
    -- Epistemic Metadata (Phase 1)
    epistemic_score FLOAT,
    reasoning_path TEXT,
    
    -- Evidence & Audit (Phase 2)
    citations JSONB, -- Stores source names, pages, and chunk hashes
    
    -- Knowledge Lifecycle (Phase 3)
    verification_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'verified', 'rejected'
    user_notes TEXT, -- Professional annotations by the researcher
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Performance Indices
CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_history(session_id);
CREATE INDEX IF NOT EXISTS idx_research_session ON research_entries(session_id);
CREATE INDEX IF NOT EXISTS idx_verification ON research_entries(verification_status);