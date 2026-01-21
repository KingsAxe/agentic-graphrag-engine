### Sovereign Research Engine
The Decoupled Sovereignty Pattern for High-Fidelity Knowledge Synthesis

1. **Introduction**
The Sovereign Research Engine is a local-first, privacy-preserving Retrieval-Augmented Generation (RAG) system designed for high-stakes research environments. Unlike traditional "chatbots" that prioritize conversational fluidity, this engine prioritizes epistemic integrity, data sovereignty, and auditability.

It operates on the "Decoupled Sovereignty Pattern," an architectural approach that separates the reasoning logic (Python/LLM) from the persistent memory (PostgreSQL) and the user interface (Tauri). This ensures that the researcher retains absolute ownership of their data, models, and crystallized knowledge, independent of cloud providers or API availability.

2. **Architectural Philosophy**
Current Generative AI systems suffer from "contextual amnesia" and "hallucination opacity." They treat answers as ephemeral and unquestionable. This engine introduces three core shifts in RAG design:

From Chat to Research: Conversations are not just logs; they are potential knowledge nodes. The system includes a "Crystallization" layer where verified answers are promoted to a permanent "Lab Notebook" state.

Epistemic Transparency: Every generation is accompanied by a Belief Report, a structured self-audit where the model scores its own confidence and highlights gaps in the retrieved evidence.

Hybrid Intent Retrieval: Recognizing that different research questions require different search strategies, the engine employs an ensemble of Dense Vector Search (Semantic), Sparse BM25 (Keyword), and Multi-Query Expansion.

3. **System Architecture**
The application follows the Sidecar Pattern, ensuring robust isolation between the user interface and the computational backend.

3.1 The Host (Tauri/Rust)
Role: Application lifecycle management, windowing, and OS-level security.

Function: Spawns the Python engine as a child process and manages the local IPC (Inter-Process Communication) bridge. It ensures the application operates strictly offline by blocking external network requests at the binary level.

3.2 The Engine (Python/FastAPI)
Role: The stateless reasoning core.

**Components:**

Orchestration: LangChain Expression Language (LCEL) for defining deterministic cognitive graphs.

Inference: llama-cpp-python for running quantized SLMs (e.g., Llama 3, Qwen 2.5) on consumer CPUs/GPUs.

API: A FastAPI server exposing endpoints for ingestion, querying, and verification solely to the local loopback (127.0.0.1).

3.3 The Vault (PostgreSQL/pgvector)
Role: The stateful memory layer.

Function: Acts as the single source of truth for:

Vector Embeddings: 384-dimensional dense vectors (BGE-Small).

Relational Metadata: Source citations, page numbers, and hashes.

Crystallized Knowledge: The research_entries table containing user-verified facts.

4. **Key Capabilities**
Epistemic Audit Layer
The engine does not output raw text. It outputs a structured ResearchResponse object containing:

Answer: The synthesized response.

Epistemic Score: A float (0.0 - 1.0) indicating the model's internal confidence based on evidence alignment.

Reasoning Trace: A "Chain of Thought" exposing the logical steps taken to reach the conclusion.

Hybrid Retrieval Modes
Precision Mode: Utilizes a weighted ensemble of Vector Similarity (60%) and BM25 Keyword Search (40%). Ideal for specific fact-checking and technical retrieval.

Exploratory Mode: Utilizes Multi-Query Expansion, where the LLM generates three variations of the user's prompt to capture broader conceptual relationships.

Recursive Grounding
The system implements a "Knowledge Feedback Loop." When a researcher verifies an answer, it is saved to the research_entries table. Subsequent queries prioritize this verified knowledge over raw document chunks, allowing the system to "learn" and refine its accuracy over time without model fine-tuning.

5. **Installation & Setup**
Prerequisites
Python 3.10+

PostgreSQL 15+ (with pgvector extension installed)

Rust & Cargo (for building the Tauri frontend)

Node.js (for building the UI assets)

Initialization
Clone the Repository:

Bash

git clone https://github.com/your-org/sovereign-research-engine.git
cd sovereign-research-engine
Environment Configuration: Create a .env file in the root directory:

**Code snippet**

DATABASE_URL=
EMBEDDING_MODEL_PATH=
Database Migration: Initialize the schema to set up vector tables and research logs.

Bash

psql -d vectors -f app/database/schema.sql
Model Acquisition: Place your .gguf model weights in models/llms/ and embedding models in models/embeddings/.

Launch (Development Mode):

Backend: uvicorn app.api:app --reload

Frontend: npm run tauri dev

6. **Usage Workflow**
Ingestion: Upload PDF research papers via the "Ingest" tab. The system performs SHA-256 hashing to prevent duplicate indexing.

Querying: Select your mode (Precision vs. Exploratory) and input your query.

Review: Examine the "Belief Report" attached to the answer.

Crystallization: If the answer is accurate, click "Verify". This commits the finding to the Lab Notebook, reinforcing the system's future performance.

7. **Contribution**
This project adheres to strict architectural standards to maintain sovereignty and modularity.

Stateless Logic: Ensure all new chains in rag_chain.py remain stateless.

Type Safety: All API exchanges must be defined via Pydantic models.

Database First: All state must persist in PostgreSQL; no in-memory session storage.

8. **License**
Distributed under the MIT License. See LICENSE for more information.