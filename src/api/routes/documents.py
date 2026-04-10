import logging
import os
import aiofiles
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, desc
from neo4j.exceptions import ServiceUnavailable
from src.api.auth import get_current_workspace
from src.models.workspace import Workspace
from src.models.document import Document, IngestionJob, JobStatus
from src.db.postgres import get_db
from src.tasks.ingestion_tasks import process_document_task
from src.services.qdrant_service import QdrantService
from src.services.neo4j_service import Neo4jService
from src.core.config import settings

router = APIRouter(prefix="/documents", tags=["Documents"])
logger = logging.getLogger(__name__)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.endswith((".pdf", ".txt")):
        logger.warning("Rejected upload for workspace %s due to unsupported file type: %s", workspace.id, file.filename)
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")

    duplicate_stmt = select(Document).where(
        Document.workspace_id == workspace.id,
        Document.filename == file.filename,
    )
    duplicate_result = await db.execute(duplicate_stmt)
    existing_document = duplicate_result.scalars().first()
    if existing_document:
        logger.warning(
            "Rejected duplicate upload for workspace %s and filename %s",
            workspace.id,
            file.filename,
        )
        raise HTTPException(
            status_code=409,
            detail="A document with this filename already exists in the current workspace. Reset the workspace or rename the file before uploading again.",
        )

    # 1. Save file locally for the worker
    file_path = os.path.join(UPLOAD_DIR, f"{workspace.id}_{file.filename}")
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    logger.info("Stored upload for workspace %s at %s", workspace.id, file_path)

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
    logger.info("Queued ingestion job %s for document %s", job.id, doc.id)

    return {"message": "Document uploaded and ingestion started.", "job_id": str(job.id)}

@router.get("/{job_id}/status")
async def get_job_status(
    job_id: str,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(IngestionJob)
        .join(Document, IngestionJob.document_id == Document.id)
        .where(IngestionJob.id == job_id, Document.workspace_id == workspace.id)
    )
    result = await db.execute(stmt)
    job = result.scalars().first()

    if not job:
        logger.warning("Workspace %s requested unknown job id %s", workspace.id, job_id)
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": str(job.id),
        "status": job.status,
        "error_message": job.error_message,
        "created_at": job.created_at,
        "completed_at": job.completed_at
    }


@router.post("/reset-workspace")
async def reset_workspace_data(
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Document.id).where(Document.workspace_id == workspace.id)
    result = await db.execute(stmt)
    document_ids = [row[0] for row in result.all()]

    await QdrantService.delete_workspace_chunks(str(workspace.id))

    neo4j_cleared = True
    try:
        await Neo4jService.delete_workspace_graph(str(workspace.id))
    except ServiceUnavailable:
        neo4j_cleared = False
        if settings.LLM_PROVIDER.lower() == "mock":
            logger.warning("Neo4j is unavailable. Skipping graph reset for workspace %s in mock mode.", workspace.id)
        else:
            raise

    if document_ids:
        await db.execute(delete(IngestionJob).where(IngestionJob.document_id.in_(document_ids)))
    await db.execute(delete(Document).where(Document.workspace_id == workspace.id))
    await db.commit()

    deleted_uploads = 0
    prefix = f"{workspace.id}_"
    for name in os.listdir(UPLOAD_DIR):
        if name.startswith(prefix):
            os.remove(os.path.join(UPLOAD_DIR, name))
            deleted_uploads += 1

    logger.info("Reset workspace %s data", workspace.id)
    return {
        "message": "Workspace data reset.",
        "workspace_id": str(workspace.id),
        "deleted_documents": len(document_ids),
        "deleted_upload_files": deleted_uploads,
        "neo4j_cleared": neo4j_cleared,
    }


@router.get("/recent")
async def get_recent_documents(
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Document, IngestionJob)
        .outerjoin(IngestionJob, IngestionJob.document_id == Document.id)
        .where(Document.workspace_id == workspace.id)
        .order_by(desc(Document.created_at))
        .limit(20)
    )
    result = await db.execute(stmt)
    rows = result.all()

    items = []
    for document, job in rows:
        items.append(
            {
                "document_id": str(document.id),
                "filename": document.filename,
                "mime_type": document.mime_type,
                "created_at": document.created_at,
                "job": None if job is None else {
                    "job_id": str(job.id),
                    "status": job.status,
                    "error_message": job.error_message,
                    "created_at": job.created_at,
                    "completed_at": job.completed_at,
                },
            }
        )

    return {
        "workspace_id": str(workspace.id),
        "documents": items,
    }
