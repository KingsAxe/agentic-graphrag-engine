# Local Development Runbook

This project now defaults to a local `mock` provider for development so you can run the stack without downloading any LLM or embedding model.

## 1. Start infrastructure

Run the backing services with Docker:

```powershell
docker compose up -d
```

This starts:

* PostgreSQL on `localhost:5433`
* Redis on `localhost:6379`
* Neo4j on `localhost:7687`
* Qdrant on `localhost:6333`

## 2. Use mock mode

Keep `LLM_PROVIDER=mock` in `.env`.

In mock mode the project uses:

* deterministic local embeddings
* heuristic graph extraction
* heuristic contradiction detection
* a mock query agent that still reads from Qdrant and Neo4j

## 3. Install Python dependencies

Create and activate a virtual environment, then install the requirements:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 4. Bootstrap the workspace and database tables

```powershell
python create_workspace.py
```

This creates the development workspace and prints the test API key.

## 5. Run the API

```powershell
uvicorn src.api.main:app --reload
```

Check readiness:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/
```

## 6. Run the Celery worker

Open a second terminal in the project root:

```powershell
celery -A src.core.celery_app:celery_app worker --loglevel=info
```

## 7. Verify the stack

Run the included verification scripts after the services are up:

```powershell
python tests\verify_week_04.py
python tests\verify_week_05.py
```

## Notes

* Mock mode is for infrastructure and workflow development, not final reasoning quality.
* If network and disk constraints improve later, move to Ollama first and Groq after that.
* To switch back to Groq later, set `LLM_PROVIDER=groq`, fill `GROQ_API_KEY`, and choose a Groq-supported model.
* The frontend expects the backend on `http://127.0.0.1:8000` by default and is allowed by CORS through `FRONTEND_ORIGINS`.
