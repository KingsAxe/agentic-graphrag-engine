import logging
import asyncio
from neo4j.exceptions import ServiceUnavailable
from src.core.celery_app import celery_app
from src.core.config import settings
from src.services.ingestion.parser import DocumentParser
from src.services.ingestion.chunker import TextChunker
from src.services.ingestion.embedder import get_embedder
from src.services.qdrant_service import QdrantService
from src.services.graph.extractor import get_graph_extractor
from src.services.neo4j_service import Neo4jService
from src.db.postgres import async_session
from src.models.document import IngestionJob, JobStatus
from sqlalchemy import update
import datetime

logger = logging.getLogger(__name__)

async def _process_document_async(job_id: str, document_id: str, workspace_id: str, file_path: str, mime_type: str):
    try:
        logger.info("Starting ingestion job %s for document %s in workspace %s", job_id, document_id, workspace_id)
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
        
        # 4. Embed Chunks & Vector Store
        logger.info(f"Embedding {len(chunks)} chunks for document {document_id}")
        embedder = get_embedder()
        embeddings = embedder.embed_texts(chunks)
        
        logger.info(f"Upserting embeddings to Qdrant")
        await QdrantService.init_collection()
        await QdrantService.upsert_chunks(workspace_id, document_id, chunks, embeddings)

        # 5. Graph Extraction (Neo4j)
        logger.info(f"Commencing LLM Graph Extraction for {len(chunks)} chunks")
        extractor = get_graph_extractor()
        for i, chunk in enumerate(chunks):
            logger.info("Processing extraction for chunk %s of %s", i + 1, len(chunks))
            try:
                # 5a. Merge the chunk node in Neo4j
                await Neo4jService.merge_chunk(workspace_id, document_id, i, chunk)
                
                # 5b. Extract Entities, Relations, Claims via LLM
                extraction = extractor.extract_from_text(chunk)
                
                # 5c. Inject into Graph
                await Neo4jService.insert_extraction(workspace_id, document_id, i, extraction)
            except ServiceUnavailable:
                if settings.LLM_PROVIDER.lower() == "mock":
                    logger.warning(
                        "Neo4j is unavailable. Skipping graph writes for chunk %s in mock mode.",
                        i + 1,
                    )
                    continue
                raise
        
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
        logger.exception("Job %s failed", job_id)
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
    asyncio.run(_process_document_async(job_id, document_id, workspace_id, file_path, mime_type))
