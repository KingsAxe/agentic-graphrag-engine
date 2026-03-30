import logging
import asyncio
from src.core.celery_app import celery_app
from src.services.ingestion.parser import DocumentParser
from src.services.ingestion.chunker import TextChunker
from src.services.ingestion.embedder import get_embedder
from src.services.qdrant_service import QdrantService
from src.db.postgres import async_session
from src.models.document import IngestionJob, JobStatus
from sqlalchemy import update
import datetime

logger = logging.getLogger(__name__)

async def _process_document_async(job_id: str, document_id: str, workspace_id: str, file_path: str, mime_type: str):
    try:
        # 1. Update Job Status to Processing
        async with async_session() as session:
            await session.execute(
                update(IngestionJob).where(IngestionJob.id == job_id).values(status=JobStatus.PROCESSING)
            )
            await session.commit()
            
        # 2. Parse File
        logger.info(f"Parsing document {document_id}")
        text = DocumentParser.parse_file(file_path, mime_type)
        
        # 3. Chunk Text
        logger.info(f"Chunking document {document_id}")
        chunks = TextChunker.chunk_text(text)
        
        # 4. Embed Chunks
        logger.info(f"Embedding {len(chunks)} chunks for document {document_id}")
        embedder = get_embedder()
        embeddings = embedder.embed_texts(chunks)
        
        # 5. Store in Qdrant
        logger.info(f"Upserting embeddings to Qdrant")
        await QdrantService.init_collection()
        await QdrantService.upsert_chunks(workspace_id, document_id, chunks, embeddings)
        
        # 6. Mark Completion
        async with async_session() as session:
            await session.execute(
                update(IngestionJob).where(IngestionJob.id == job_id).values(
                    status=JobStatus.COMPLETED,
                    completed_at=datetime.datetime.utcnow()
                )
            )
            await session.commit()
            
        logger.info(f"Job {job_id} completed successfully.")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        async with async_session() as session:
            await session.execute(
                update(IngestionJob).where(IngestionJob.id == job_id).values(
                    status=JobStatus.FAILED,
                    error_message=str(e),
                    completed_at=datetime.datetime.utcnow()
                )
            )
            await session.commit()


@celery_app.task(name="process_document_task")
def process_document_task(job_id: str, document_id: str, workspace_id: str, file_path: str, mime_type: str):
    """Celery task wrapper around the async ingestion pipeline."""
    # Celery workers execute synchronous Python, so we use asyncio.run 
    asyncio.run(_process_document_async(job_id, document_id, workspace_id, file_path, mime_type))
