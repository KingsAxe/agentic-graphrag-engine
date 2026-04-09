from sentence_transformers import SentenceTransformer
import logging
from src.core.config import settings
from src.services.llm.mock import mock_embed_texts

logger = logging.getLogger(__name__)

class EmbedderService:
    def __init__(self, model_name: str = "BAAI/bge-m3"):
        logger.info(f"Loading embedding model: {model_name}")
        # Automatically downloads and caches the model on first instantiation
        self.model = SentenceTransformer(model_name)
        
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        # Return dense vectors
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()


class MockEmbedderService:
    def __init__(self):
        logger.info("Using mock embedder for local development")

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return mock_embed_texts(texts)

# Singleton instance initialized when the worker boots
embedder = None

def get_embedder() -> EmbedderService:
    global embedder
    if embedder is None:
        if settings.LLM_PROVIDER.lower() == "mock":
            embedder = MockEmbedderService()
        else:
            embedder = EmbedderService()
    return embedder
