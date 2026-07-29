from functools import lru_cache
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

from app.ai.logging.logger import AILogger
from app.core.config import settings

logger = AILogger("embeddings")


class EmbeddingService:
    """
    Reusable embedding service.
    Agents and the RAG pipeline request embeddings through this service.
    Swap the model by changing EMBEDDING_MODEL in .env — no code changes needed.
    """

    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        model = model_name or settings.EMBEDDING_MODEL
        dev = device or settings.EMBEDDING_DEVICE
        logger.info("Loading embedding model", model=model, device=dev)
        self._model = SentenceTransformer(model, device=dev)
        self._model_name = model
        self._dimension = self._model.get_sentence_embedding_dimension()
        logger.info("Embedding model loaded", dimension=self._dimension)

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed_text(self, text: str) -> List[float]:
        """Embed a single string."""
        with logger.timer("embed_text"):
            vec = self._model.encode(text, normalize_embeddings=True)
        return vec.tolist()

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Embed a list of strings efficiently."""
        with logger.timer("embed_batch", count=len(texts)):
            vecs = self._model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
        return vecs.tolist()

    def similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Cosine similarity between two embedding vectors."""
        a = np.array(vec_a)
        b = np.array(vec_b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))


# Lazy singleton — loaded only when first accessed
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
