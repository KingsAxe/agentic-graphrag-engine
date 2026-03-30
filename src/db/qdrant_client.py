from qdrant_client import AsyncQdrantClient
from src.core.config import settings

qdrant_client = AsyncQdrantClient(
    host=settings.QDRANT_HOST,
    port=settings.QDRANT_PORT
)
