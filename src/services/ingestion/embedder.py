from sentence_transformers import SentenceTransformer
import logging

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

# Singleton instance initialized when the worker boots
embedder = None

def get_embedder() -> EmbedderService:
    global embedder
    if embedder is None:
        embedder = EmbedderService()
    return embedder
