"""
Sovereign Research Engine API (FastAPI)

- Local loopback only (127.0.0.1)
- Directory-based model discovery + optional default model
- Health endpoints for backend-first testing (and later Tauri readiness)
- Clear env validation + safer path handling on Windows/packaged mode
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import os
import shutil
from dotenv import load_dotenv

# Import your existing engine logic
from app.core.model_manager import ModelManager
from app.core.ingestor import DocumentIngestor
from app.core.rag_chain import RAGEngine
from app.database.connection import get_vector_store
from app.database.research_manager import ResearchManager

import json
import psycopg2

CONFIG_FILE = os.path.join(os.getcwd(), "config.json")

def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_config(cfg: dict) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

_cfg = load_config()



# 1) Load .env variables (dev mode)
load_dotenv()

app = FastAPI(title="Sovereign Research Engine API")

# -----------------------------
# Configuration (strict)
# -----------------------------
DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    raise ValueError("DATABASE_URL not found in .env file.")

EMBED_PATH = os.getenv("EMBEDDING_MODEL_PATH")
if not EMBED_PATH:
    raise ValueError("EMBEDDING_MODEL_PATH not found in .env file.")

LLM_DIR = os.getenv("LLM_MODELS_DIR") or _cfg.get("LLM_MODELS_DIR")
if not LLM_DIR:
    raise ValueError("LLM_MODELS_DIR not found in .env file.")
LLM_DIR = os.path.abspath(LLM_DIR)if LLM_DIR else ""

# Use filename as default model (NOT a full path)
DEFAULT_MODEL = os.getenv("DEFAULT_LLM_MODEL") or _cfg.get("DEFAULT_LLM_MODEL")
DEFAULT_MODEL = os.path.basename(DEFAULT_MODEL) or ""
if not DEFAULT_MODEL:
    raise ValueError("DEFAULT_LLM_MODEL not found in .env file (expected a .gguf filename).")

# Initialize Managers (singletons for dev)
model_manager = ModelManager(models_dir=LLM_DIR) if LLM_DIR else None
res_manager = ResearchManager(DB_URL)

# Optional: initialize once (avoids re-creating on every request)
# If your get_vector_store is heavy, this is a big win for local dev.
VECTOR_STORE = get_vector_store(DB_URL, EMBED_PATH)


# -----------------------------
# Request/Response Models
# -----------------------------
class QueryRequest(BaseModel):
    input_text: str
    session_id: str
    model_name: Optional[str] = None  # optional for backend-first testing
    mode: str = "precision"


class VerificationRequest(BaseModel):
    entry_id: int
    status: str
    notes: Optional[str] = None


# -----------------------------
# Basic endpoints (dev/test)
# -----------------------------

class SettingsPayload(BaseModel):
    llm_models_dir: str
    default_llm_model: Optional[str] = None

@app.get("/settings")
async def get_settings():
    cfg = load_config()
    return {
        "llm_models_dir": cfg.get("LLM_MODELS_DIR", ""),
        "default_llm_model": cfg.get("DEFAULT_LLM_MODEL", "")
    }


@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "Sovereign Research Engine API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


# -----------------------------
# Core endpoints
# -----------------------------
@app.get("/models")
async def list_models():
    if not LLM_DIR or not os.path.isdir(LLM_DIR) or model_manager is None:
        return {"models": [], "default": DEFAULT_MODEL, "configured": False}
    return {"models": model_manager.list_available_models(), "default": DEFAULT_MODEL, "configured": True}


@app.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    """Handles PDF ingestion and vectorization."""
    try:
        os.makedirs(os.path.join("data", "raw"), exist_ok=True)

        temp_path = os.path.join("data", "raw", file.filename)
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        ingestor = DocumentIngestor(DB_URL, EMBED_PATH)
        success = ingestor.ingest(temp_path)

        if not success:
            raise HTTPException(status_code=500, detail="Ingestion failed.")
        return {"status": "success", "filename": file.filename}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion error: {e}")


@app.post("/query")
async def research_query(request: QueryRequest):
    """The main research synthesis endpoint."""
    history_manager = None
    try:
        # Choose model: request override -> default
        model_name = request.model_name or DEFAULT_MODEL

        # Validate model existence in the models dir
        model_path = os.path.join(LLM_DIR, model_name)
        if not os.path.exists(model_path):
            available = model_manager.list_available_models()
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Model '{model_name}' not found in {LLM_DIR}. "
                    f"Available: {available[:10]}{'...' if len(available) > 10 else ''}"
                ),
            )

        # 1) Load LLM
        llm = model_manager.load_model(model_name)

        # 2) Initialize Engine
        engine = RAGEngine(llm, VECTOR_STORE, DB_URL)

        # 3) Get Knowledge & History
        history_manager = engine.get_chat_history(request.session_id)
        verified_context = res_manager.get_verified_knowledge(request.session_id)

        # 4) Execute Chain
        chain = engine.create_chain(mode=request.mode, verified_knowledge=verified_context)

        response = chain.invoke(
            {
                "input": request.input_text,
                "chat_history": history_manager.messages,
                "verified_knowledge": verified_context,
            }
        )

        # 5) Auto-save to pending research entries
        entry_id = res_manager.save_entry(request.session_id, request.input_text, response)

        # 6) Persist Chat History
        history_manager.add_user_message(request.input_text)
        history_manager.add_ai_message(response.answer)

        # pydantic v2: prefer model_dump(); v1: dict()
        data = response.model_dump() if hasattr(response, "model_dump") else response.dict()

        return {"entry_id": entry_id, "data": data}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Query Error: {e}")
        raise HTTPException(status_code=500, detail=f"Query error: {e}")

    finally:
        # Close the psycopg connection we attached in RAGEngine.get_chat_history()
        if history_manager is not None:
            conn = getattr(history_manager, "_sre_conn", None)
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

@app.post("/settings")
async def update_settings(payload: SettingsPayload):
    global LLM_DIR, DEFAULT_MODEL, model_manager

    models_dir = os.path.abspath(payload.llm_models_dir)

    if not os.path.isdir(models_dir):
        raise HTTPException(status_code=400, detail=f"Directory does not exist: {models_dir}")

    # If a default model is provided, validate it exists
    default_model = payload.default_llm_model or ""
    if default_model:
        candidate = os.path.join(models_dir, default_model)
        if not os.path.exists(candidate):
            raise HTTPException(
                status_code=400,
                detail=f"Default model not found in folder: {default_model}"
            )

    cfg = load_config()
    cfg["LLM_MODELS_DIR"] = models_dir
    cfg["DEFAULT_LLM_MODEL"] = default_model
    save_config(cfg)

    # Update runtime globals + reload model manager
    LLM_DIR = models_dir
    DEFAULT_MODEL = default_model
    model_manager = ModelManager(models_dir=LLM_DIR)

    return {"status": "ok", "llm_models_dir": LLM_DIR, "default_llm_model": DEFAULT_MODEL}


from pathlib import Path

@app.get("/library")
async def library():
    """
    Shows documents known to the vector store, even if the raw PDF was deleted.
    Returns: filename, stored_path, available, chunks, max_page, preview
    """
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    # Works with LangChain PGVector tables (document + cmetadata JSONB)
    cur.execute("""
        SELECT
            COALESCE(cmetadata->>'filename', split_part(cmetadata->>'source', '/', array_length(string_to_array(cmetadata->>'source','/'),1))) AS filename,
            COALESCE(cmetadata->>'stored_path', cmetadata->>'source') AS stored_path,
            COUNT(*) AS chunks,
            MAX(NULLIF(cmetadata->>'page','')::int) AS max_page,
            LEFT(MAX(document), 400) AS preview
        FROM langchain_pg_embedding
        GROUP BY 1,2
        ORDER BY chunks DESC;
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    out = []
    for filename, stored_path, chunks, max_page, preview in rows:
        available = False
        try:
            available = Path(stored_path).exists()
        except Exception:
            available = False

        out.append({
            "filename": filename,
            "stored_path": stored_path,
            "available": available,   # file exists on disk?
            "chunks": int(chunks),
            "max_page": int(max_page) if max_page is not None else None,
            "preview": preview or "",
        })

    return {"documents": out}


@app.post("/verify")
async def verify_entry(request: VerificationRequest):
    """Crystallizes a pending entry into the Lab Notebook."""
    try:
        res_manager.verify_entry(request.entry_id, request.status, request.notes)
        return {"status": "updated", "entry_id": request.entry_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verify error: {e}")


@app.get("/notebook/{session_id}")
async def get_notebook(session_id: str):
    """Retrieves all research entries for a session."""
    try:
        return res_manager.get_session_entries(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notebook error: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
