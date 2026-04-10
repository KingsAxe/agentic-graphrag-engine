import logging
import os
import aiofiles
from uuid import UUID
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, desc, func, select as sa_select
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
JOB_NOT_FOUND_DETAIL = "Job not found in the authenticated workspace."
DUPLICATE_UPLOAD_DETAIL = (
    "A document with this filename already exists in the current workspace. "
    "Reset the workspace or rename the file before uploading again."
)
MISSING_UPLOAD_DETAIL = "The original upload is not available for retry in the authenticated workspace."

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _job_state_metadata(job: IngestionJob) -> dict:
    status_value = job.status.value if isinstance(job.status, JobStatus) else str(job.status)
    action_hint = {
        JobStatus.PENDING: "The job is queued and waiting for worker pickup.",
        JobStatus.PROCESSING: "The job is actively being processed by the worker.",
        JobStatus.COMPLETED: "The job completed successfully. The document is ready for querying.",
        JobStatus.FAILED: "The job failed. Review the error and use retry if the source file is still available.",
    }.get(job.status, "Unknown job state.")

    return {
        "job_id": str(job.id),
        "status": status_value,
        "error_message": job.error_message,
        "created_at": job.created_at,
        "completed_at": job.completed_at,
        "is_terminal": job.status in {JobStatus.COMPLETED, JobStatus.FAILED},
        "can_retry": job.status == JobStatus.FAILED,
        "action_hint": action_hint,
    }


async def _get_workspace_job(job_id: UUID, workspace: Workspace, db: AsyncSession) -> tuple[IngestionJob, Document]:
    stmt = (
        select(IngestionJob, Document)
        .join(Document, IngestionJob.document_id == Document.id)
        .where(IngestionJob.id == job_id, Document.workspace_id == workspace.id)
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        logger.warning("Workspace %s requested unknown job id %s", workspace.id, job_id)
        raise HTTPException(status_code=404, detail=JOB_NOT_FOUND_DETAIL)
    return row

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
            detail=DUPLICATE_UPLOAD_DETAIL,
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
    job_id: UUID,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    job, _document = await _get_workspace_job(job_id, workspace, db)
    return _job_state_metadata(job)


@router.post("/{job_id}/retry")
async def retry_job(
    job_id: UUID,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    job, document = await _get_workspace_job(job_id, workspace, db)

    if job.status not in {JobStatus.FAILED, JobStatus.COMPLETED}:
        raise HTTPException(status_code=409, detail="Only failed or completed jobs can be retried.")

    file_path = os.path.join(UPLOAD_DIR, f"{workspace.id}_{document.filename}")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=MISSING_UPLOAD_DETAIL)

    retry_job = IngestionJob(document_id=document.id, status=JobStatus.PENDING)
    db.add(retry_job)
    await db.commit()
    await db.refresh(retry_job)

    process_document_task.delay(
        job_id=str(retry_job.id),
        document_id=str(document.id),
        workspace_id=str(workspace.id),
        file_path=file_path,
        mime_type=document.mime_type,
    )
    logger.info("Queued retry job %s for original job %s in workspace %s", retry_job.id, job.id, workspace.id)

    return {
        "message": "Retry queued.",
        "workspace_id": str(workspace.id),
        "source_job_id": str(job.id),
        "retry_job": _job_state_metadata(retry_job),
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
    latest_job_per_document = (
        sa_select(
            IngestionJob.document_id.label("document_id"),
            func.max(IngestionJob.created_at).label("latest_created_at"),
        )
        .group_by(IngestionJob.document_id)
        .subquery()
    )

    stmt = (
        select(Document, IngestionJob)
        .outerjoin(latest_job_per_document, latest_job_per_document.c.document_id == Document.id)
        .outerjoin(
            IngestionJob,
            (IngestionJob.document_id == Document.id)
            & (IngestionJob.created_at == latest_job_per_document.c.latest_created_at),
        )
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
                "job": None if job is None else _job_state_metadata(job),
            }
        )

    return {
        "workspace_id": str(workspace.id),
        "documents": items,
    }
