import os
import json
import uuid
from typing import List, Dict, Any, Optional, Tuple

import faiss
import numpy as np

from app.core.config import settings
from app.ai.logging.logger import AILogger

logger = AILogger("rag.faiss")


class FAISSVectorStore:
    """
    FAISS-backed vector store with metadata persistence.
    Modular design — swap FAISS for another vector DB by implementing the same interface.
    """

    def __init__(
        self,
        dimension: int,
        store_dir: Optional[str] = None,
        index_name: Optional[str] = None,
    ):
        self._dim = dimension
        self._dir = store_dir or settings.VECTOR_STORE_DIR
        self._name = index_name or settings.VECTOR_STORE_INDEX_NAME
        self._index_path = os.path.join(self._dir, f"{self._name}.faiss")
        self._meta_path = os.path.join(self._dir, f"{self._name}.json")

        os.makedirs(self._dir, exist_ok=True)

        # id_map keeps FAISS integer IDs → chunk metadata
        self._id_map: Dict[int, Dict[str, Any]] = {}
        self._index: faiss.Index = self._build_index()

    # ── Index lifecycle ───────────────────────────────────────────────────────

    def _build_index(self) -> faiss.Index:
        """Inner-product index (works with L2-normalized vectors = cosine similarity)."""
        return faiss.IndexIDMap(faiss.IndexFlatIP(self._dim))

    def save(self) -> None:
        faiss.write_index(self._index, self._index_path)
        with open(self._meta_path, "w") as f:
            json.dump({str(k): v for k, v in self._id_map.items()}, f)
        logger.info("Vector store saved", path=self._index_path, vectors=self._index.ntotal)

    def load(self) -> bool:
        """Load index from disk. Returns True if successful."""
        if not os.path.exists(self._index_path):
            logger.info("No existing index found, starting fresh")
            return False
        self._index = faiss.read_index(self._index_path)
        if os.path.exists(self._meta_path):
            with open(self._meta_path) as f:
                raw = json.load(f)
            self._id_map = {int(k): v for k, v in raw.items()}
        logger.info("Vector store loaded", path=self._index_path, vectors=self._index.ntotal)
        return True

    def reset(self) -> None:
        """Clear the index and metadata."""
        self._index = self._build_index()
        self._id_map = {}
        logger.info("Vector store reset")

    # ── Write operations ──────────────────────────────────────────────────────

    def add(
        self,
        vectors: List[List[float]],
        metadata: List[Dict[str, Any]],
    ) -> List[str]:
        """
        Add vectors with associated metadata.
        Returns list of assigned chunk IDs.
        """
        if len(vectors) != len(metadata):
            raise ValueError("vectors and metadata must have the same length")

        np_vecs = np.array(vectors, dtype=np.float32)
        # Assign sequential integer IDs starting after current max
        start_id = self._index.ntotal
        ids = np.arange(start_id, start_id + len(vectors), dtype=np.int64)

        self._index.add_with_ids(np_vecs, ids)

        chunk_ids: List[str] = []
        for i, meta in enumerate(metadata):
            cid = meta.get("chunk_id") or str(uuid.uuid4())
            self._id_map[int(ids[i])] = {**meta, "chunk_id": cid}
            chunk_ids.append(cid)

        logger.debug("Vectors added", count=len(vectors), total=self._index.ntotal)
        return chunk_ids

    # ── Search ────────────────────────────────────────────────────────────────

    def search(
        self,
        query_vector: List[float],
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Similarity search. Returns list of {score, chunk_id, ...metadata} dicts.
        """
        k = top_k or settings.RAG_TOP_K
        min_score = threshold if threshold is not None else settings.RAG_SIMILARITY_THRESHOLD

        if self._index.ntotal == 0:
            return []

        k = min(k, self._index.ntotal)
        query = np.array([query_vector], dtype=np.float32)
        scores, ids = self._index.search(query, k)

        results: List[Dict[str, Any]] = []
        for score, idx in zip(scores[0], ids[0]):
            if idx == -1 or float(score) < min_score:
                continue
            meta = self._id_map.get(int(idx), {})
            results.append({"score": round(float(score), 4), **meta})

        logger.debug("Vector search completed", results=len(results), top_k=k)
        return results

    @property
    def total_vectors(self) -> int:
        return self._index.ntotal

    @property
    def dimension(self) -> int:
        return self._dim


# ── Lazy singleton ────────────────────────────────────────────────────────────

_vector_store: Optional[FAISSVectorStore] = None


def get_vector_store(dimension: Optional[int] = None) -> FAISSVectorStore:
    global _vector_store
    if _vector_store is None:
        from app.ai.rag.embedding_service import get_embedding_service
        dim = dimension or get_embedding_service().dimension
        _vector_store = FAISSVectorStore(dimension=dim)
        _vector_store.load()
    return _vector_store
