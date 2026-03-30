from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.api.auth import get_current_workspace
from src.models.workspace import Workspace
from src.models.document import Document, IngestionJob, JobStatus
from src.db.postgres import get_db
from src.tasks.ingestion_tasks import process_document_task
import os
import aiofiles

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.endswith((".pdf", ".txt")):
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")

    # 1. Save file locally for the worker
    file_path = os.path.join(UPLOAD_DIR, f"{workspace.id}_{file.filename}")
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    # 2. Create DB Records (Document & Job)
    doc = Document(workspace_id=workspace.id, filename=file.filename, mime_type=file.content_type)
    db.add(doc)
    await db.flush()  # To get doc.id

    job = IngestionJob(document_id=doc.id, status=JobStatus.PENDING)
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # 3. Dispatch Celery Task
    process_document_task.delay(
        job_id=str(job.id),
        document_id=str(doc.id),
        workspace_id=str(workspace.id),
        file_path=file_path,
        mime_type=file.content_type
    )

    return {"message": "Document uploaded and ingestion started.", "job_id": str(job.id)}

@router.get("/{job_id}/status")
async def get_job_status(
    job_id: str,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(IngestionJob).where(IngestionJob.id == job_id)
    result = await db.execute(stmt)
    job = result.scalars().first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": str(job.id),
        "status": job.status,
        "error_message": job.error_message,
        "created_at": job.created_at,
        "completed_at": job.completed_at
    }
