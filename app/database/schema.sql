-- Enable the vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Document Metadata (The "Knowledge Source")
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL,
    file_hash TEXT UNIQUE NOT NULL, -- SHA-256 to prevent duplicates
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB                  -- Store page counts, author, etc.
);

-- 2. Document Chunks (The "Semantic Layer")
CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(384),          -- 384 for 'all-MiniLM-L6-v2'
    page_number INTEGER
);

-- 3. Chat Sessions & History (The "Memory Layer")
CREATE TABLE IF NOT EXISTS chat_history (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,       -- Unique ID for each chat window
    role TEXT NOT NULL,             -- 'user' or 'assistant'
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create an HNSW index for fast vector search (Scale-ready)
CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops);