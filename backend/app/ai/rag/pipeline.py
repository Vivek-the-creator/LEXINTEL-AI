from typing import List, Dict, Any, Optional

from app.ai.rag.chunker import TextChunker, DocumentChunkResult
from app.ai.rag.embedding_service import EmbeddingService, get_embedding_service
from app.ai.rag.faiss_store import FAISSVectorStore, get_vector_store
from app.ai.logging.logger import AILogger
from app.core.config import settings

logger = AILogger("rag.pipeline")


class RAGPipeline:
    """
    End-to-end Retrieval-Augmented Generation pipeline.
    Orchestrates: chunk → embed → index → retrieve.
    Generic enough to support any document type in Phase 3.
    """

    def __init__(
        self,
        embedder: Optional[EmbeddingService] = None,
        store: Optional[FAISSVectorStore] = None,
        chunker: Optional[TextChunker] = None,
    ):
        self._embedder = embedder or get_embedding_service()
        self._store = store or get_vector_store(self._embedder.dimension)
        self._chunker = chunker or TextChunker()

    # ── Indexing ──────────────────────────────────────────────────────────────

    def index_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        persist: bool = True,
    ) -> List[str]:
        """Chunk, embed, and index a raw text string. Returns chunk IDs."""
        chunks = self._chunker.chunk_text(text, metadata=metadata)
        return self._index_chunks(chunks, persist=persist)

    def index_documents(
        self,
        documents: List[Dict[str, Any]],
        text_field: str = "text",
        persist: bool = True,
    ) -> List[str]:
        """Chunk, embed, and index a list of document dicts. Returns chunk IDs."""
        chunks = self._chunker.chunk_documents(documents, text_field=text_field)
        return self._index_chunks(chunks, persist=persist)

    def _index_chunks(
        self,
        chunks: List[DocumentChunkResult],
        persist: bool = True,
    ) -> List[str]:
        if not chunks:
            return []

        texts = [c.text for c in chunks]
        vectors = self._embedder.embed_batch(texts)
        metadata = [
            {"chunk_id": c.chunk_id, "text": c.text, **c.metadata}
            for c in chunks
        ]
        chunk_ids = self._store.add(vectors, metadata)

        if persist:
            self._store.save()

        logger.info("Documents indexed", chunks=len(chunks))
        return chunk_ids

    # ── Retrieval ─────────────────────────────────────────────────────────────

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Embed query and return top-k similar chunks."""
        query_vec = self._embedder.embed_text(query)
        results = self._store.search(query_vec, top_k=top_k, threshold=threshold)
        logger.debug("Retrieval completed", query_len=len(query), results=len(results))
        return results

    def retrieve_context(
        self,
        query: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> str:
        """Retrieve and format chunks into a single context string for LLM prompts."""
        results = self.retrieve(query, top_k=top_k, threshold=threshold)
        if not results:
            return ""
        parts = [f"[{i+1}] (score={r['score']}) {r.get('text', '')}" for i, r in enumerate(results)]
        return "\n\n".join(parts)

    @property
    def total_indexed(self) -> int:
        return self._store.total_vectors


# ── Lazy singleton ────────────────────────────────────────────────────────────

_rag_pipeline: Optional[RAGPipeline] = None


def get_rag_pipeline() -> RAGPipeline:
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline
