from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    Filter,
    FieldCondition,
    MatchAny,
    MatchValue,
)
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
    async def search_chunks(
        workspace_id: str,
        query_vector: list[float],
        limit: int = 5,
        document_ids: list[str] | None = None,
    ):
        """Search for similar chunks within a specific workspace and optional document scope."""
        must_conditions = [
            FieldCondition(
                key="workspace_id",
                match=MatchValue(value=str(workspace_id)),
            )
        ]

        scoped_document_ids = [str(document_id) for document_id in (document_ids or []) if document_id]
        if scoped_document_ids:
            if len(scoped_document_ids) == 1:
                must_conditions.append(
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=scoped_document_ids[0]),
                    )
                )
            else:
                must_conditions.append(
                    FieldCondition(
                        key="document_id",
                        match=MatchAny(any=scoped_document_ids),
                    )
                )

        search_result = await qdrant_client.search(
            collection_name=QdrantService.COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=Filter(must=must_conditions),
            limit=limit,
        )
        return [
            {
                "text": hit.payload["text"],
                "score": hit.score,
                "document_id": hit.payload.get("document_id"),
                "chunk_index": hit.payload.get("chunk_index"),
            }
            for hit in search_result
        ]

    @staticmethod
    async def delete_workspace_chunks(workspace_id: str):
        exists = await qdrant_client.collection_exists(QdrantService.COLLECTION_NAME)
        if not exists:
            return

        await qdrant_client.delete(
            collection_name=QdrantService.COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="workspace_id",
                        match=MatchValue(value=str(workspace_id)),
                    )
                ]
            ),
            wait=True,
        )
