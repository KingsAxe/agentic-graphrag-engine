from qdrant_client.models import VectorParams, Distance, PointStruct, Filter, FieldCondition, MatchValue
from src.db.qdrant_client import qdrant_client
import uuid

class QdrantService:
    COLLECTION_NAME = "documents"

    @staticmethod
    async def init_collection(vector_size: int = 1024):
        """Initialize the Qdrant collection if it doesn't exist. 1024 for BGE-M3."""
        exists = await qdrant_client.collection_exists(QdrantService.COLLECTION_NAME)
        if not exists:
            await qdrant_client.create_collection(
                collection_name=QdrantService.COLLECTION_NAME,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

    @staticmethod
    async def upsert_chunks(workspace_id: str, document_id: str, chunks: list[str], embeddings: list[list[float]]):
        """Insert embedded chunks into Qdrant with metadata payload."""
        if not chunks or not embeddings:
            return

        points = []
        for i, (chunk, vector) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid.uuid4())
            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "workspace_id": str(workspace_id),
                        "document_id": str(document_id),
                        "chunk_index": i,
                        "text": chunk
                    }
                )
            )

        await qdrant_client.upsert(
            collection_name=QdrantService.COLLECTION_NAME,
            points=points
        )

    @staticmethod
    async def search_chunks(workspace_id: str, query_vector: list[float], limit: int = 5):
        """Search for similar chunks within a specific workspace."""
        search_result = await qdrant_client.search(
            collection_name=QdrantService.COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="workspace_id",
                        match=MatchValue(value=str(workspace_id)),
                    )
                ]
            ),
            limit=limit,
        )
        return [{"text": hit.payload["text"], "score": hit.score} for hit in search_result]
