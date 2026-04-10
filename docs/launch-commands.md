# Launch Commands

Run these from `C:\Users\pc\Desktop\Pro_Jets\local-rag-engine-v2`.

## 1. Activate the virtual environment

```powershell
.\RagV2\Scripts\Activate.ps1
```

## 2. Start infrastructure

```powershell
docker compose up -d
```

## 3. Bootstrap the workspace

```powershell
python create_workspace.py
```

## 4. Start the API

```powershell
uvicorn src.api.main:app --reload
```

## 5. Start the worker in another terminal

```powershell
.\RagV2\Scripts\Activate.ps1
celery -A src.core.celery_app:celery_app worker --pool=solo --loglevel=info
```

## 6. Useful helper scripts

Upload the sample file:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\upload_sample.ps1
```

Check a job:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_job.ps1 -JobId <JOB_ID>
```

Reset the development workspace:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\reset_workspace.ps1
```

## 7. Start the frontend

Open another terminal:

```powershell
cd .\frontend
copy .env.example .env.local
npm install
npm run dev
```

The frontend will run on `http://localhost:3000`.

## 8. Run Week 7 verification

After the API, worker, and databases are running:

```powershell
.\RagV2\Scripts\python.exe tests\verify_week_07.py
.\RagV2\Scripts\python.exe tests\verify_week_07_workspace_isolation.py
```
