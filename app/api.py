"""
FastAPI + Pydantic: By using the .dict() method on your ResearchResponse, the API automatically converts your complex "Belief Report" and "Citations" into a clean JSON object that a frontend (React/Svelte) can easily parse.

Concurrency Ready: FastAPI is asynchronous. While the LLM inference is synchronous (blocking), the API can still handle incoming metadata requests or document uploads without freezing the whole system.

Local Loopback Only: By forcing host="127.0.0.1", you ensure that even if a user is on a public Wi-Fi, no one else can "hit" your research engine. It remains truly sovereign and private.
"""



from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
import os
import shutil

# Import your existing engine logic
from core.model_manager import ModelManager
from core.ingestor import DocumentIngestor
from core.rag_chain import RAGEngine
from database.connection import get_vector_store
from database.research_manager import ResearchManager

app = FastAPI(title="Sovereign Research Engine API")

# --- Configuration ---
DB_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/vectors")
EMBED_PATH = os.getenv("EMBEDDING_MODEL_PATH", "models/embeddings/bge-small-en-v1.5")
model_manager = ModelManager()
res_manager = ResearchManager(DB_URL)

# --- Request/Response Models ---
class QueryRequest(BaseModel):
    input_text: str
    session_id: str
    mode: str = "precision"

class VerificationRequest(BaseModel):
    entry_id: int
    status: str
    notes: Optional[str] = None

# --- Endpoints ---

@app.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    """Handles PDF ingestion and vectorization."""
    try:
        temp_path = f"data/raw/{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        ingestor = DocumentIngestor(DB_URL, EMBED_PATH)
        success = ingestor.ingest(temp_path)
        
        if not success:
            raise HTTPException(status_code=500, detail="Ingestion failed.")
        return {"status": "success", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def research_query(request: QueryRequest):
    """The main research synthesis endpoint."""
    try:
        # 1. Initialize Engine
        # In production, we'd use a specific model file from config
        llm = model_manager.load_model("llama-3.1-8b-q4_k_m.gguf") 
        vector_store = get_vector_store(DB_URL, EMBED_PATH)
        engine = RAGEngine(llm, vector_store, DB_URL)
        
        # 2. Get Knowledge & History
        history_manager = engine.get_chat_history(request.session_id)
        verified_context = res_manager.get_verified_knowledge(request.session_id)
        
        # 3. Execute Chain
        chain = engine.create_chain(mode=request.mode)
        response = chain.invoke({
            "input": request.input_text,
            "chat_history": history_manager.messages,
            "verified_knowledge": verified_context
        })
        
        # 4. Auto-save to pending research entries
        entry_id = res_manager.save_entry(request.session_id, request.input_text, response)
        
        # 5. Persist Chat History
        history_manager.add_user_message(request.input_text)
        history_manager.add_ai_message(response.answer)
        
        return {
            "entry_id": entry_id,
            "data": response.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/verify")
async def verify_entry(request: VerificationRequest):
    """Crystallizes a pending entry into the Lab Notebook."""
    res_manager.verify_entry(request.entry_id, request.status, request.notes)
    return {"status": "updated", "entry_id": request.entry_id}

@app.get("/notebook/{session_id}")
async def get_notebook(session_id: str):
    """Retrieves all research entries for a session."""
    return res_manager.get_session_entries(session_id)

if __name__ == "__main__":
    import uvicorn
    # Only listen on localhost for security in the Tauri sidecar pattern
    uvicorn.run(app, host="127.0.0.1", port=8000)