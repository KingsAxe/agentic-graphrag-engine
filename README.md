# 🧠 Local Knowledge Engine (Offline RAG)

A private-by-design RAG system that turns local PDFs into a persistent knowledge base. Built for researchers and developers who need high-performance AI without data leaks.

## 🌟 Key Features
- **Deterministic Ingestion**: SHA-256 hashing prevents duplicate processing of the same document.
- **Persistent Memory**: Uses PostgreSQL + `pgvector` for long-term chat history and document storage.
- **Model Registry**: Swap LLMs (Llama 3, Mistral, etc.) by dropping `.gguf` files into a folder.
- **Production Ready**: Full Docker orchestration and Render-compatible structure.

## 🛠️ Tech Stack
- **UI**: Streamlit (White/Gray Professional Theme)
- **Database**: Postgres + pgvector
- **Orchestration**: LangChain
- **Embeddings**: BGE-small-en-v1.5 (Local path registered)
- **Inference**: llama-cpp-python

## 🚀 Local Setup (Fully Offline)

### 1. Model Preparation
1. **Embeddings**: Download [BGE-small-en-v1.5](https://huggingface.co/BAAI/bge-small-en-v1.5) and place files in `./models/embeddings/bge-small-en-v1.5/`.
2. **LLM**: Download any GGUF (e.g., Llama-3-8B) and place it in `./models/llm/`.

### 2. Launch Infrastructure
```bash
docker-compose up -d

**3. Run Application**

pip install -r requirements.txt
streamlit run app/main.py


---

## 3. The Offline "Gold Standard" Setup Procedure

Since you are currently in your IDE and want to test this extensively, follow these exact steps to ensure "offline" means "offline."

### Step A: Initialize the Database
Run `docker-compose up -d`. This starts your Postgres container. 
* **Verification**: Open your terminal and run `docker exec -it rag_db psql -U admin -d knowledge_db -c "SELECT * FROM pg_extension WHERE extname='vector';"`. If it returns a row, your vector store is ready.

### Step B: Download Model Assets
You must manually download these for a true offline build:
1.  **BGE Embeddings**: Use `git clone https://huggingface.co/BAAI/bge-small-en-v1.5` inside your `/models/embeddings/` folder.
2.  **LLM**: Download a quantized GGUF file (like `Llama-3-8B-Instruct-Q4_K_M.gguf`) from Hugging Face and put it in `/models/llm/`.

### Step C: Installation (The "C-Compiler" Note)
Because we use `llama-cpp-python`, you need a C++ compiler on your machine.
* **Mac**: `xcode-select --install`
* **Windows**: Install "Desktop Development with C++" via Visual Studio Installer.

* **Linux**: `sudo apt install build-essential`

### Step D: Testing Protocol (Extensive)
To test if it's "Paper-Worthy," perform these three tests:
1.  **The Duplication Test**: Upload "Document_A.pdf". Then upload it again. The UI should show "Knowledge base updated" (or your custom skip message), and the database should NOT have duplicate chunks.
2.  **The Continuity Test**: Ask a question about the PDF. Close the browser. Re-open it. Your previous question and answer should still be there (retrieved from Postgres).
3.  **The "Cold Swap" Test**: Drop a new GGUF file in the folder. Use the sidebar to switch models. Ask the same question and observe if the writing style changes.

**Would you like me to provide a specialized `Dockerfile` for the Streamlit app itself, optimized for a local environment with GPU/CPU auto-detection?**