import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.ai.logging.logger import AILogger

logger = AILogger("rag.chunker")


@dataclass
class DocumentChunkResult:
    chunk_id: str
    text: str
    chunk_index: int
    total_chunks: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class TextChunker:
    """
    Splits text into overlapping chunks for embedding and retrieval.
    Chunk size and overlap are configurable via settings.
    """

    def __init__(
        self,
        chunk_size: int = 0,
        chunk_overlap: int = 0,
    ):
        self._chunk_size = chunk_size or settings.RAG_CHUNK_SIZE
        self._chunk_overlap = chunk_overlap or settings.RAG_CHUNK_OVERLAP

    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunkResult]:
        """Split text into overlapping chunks."""
        text = text.strip()
        if not text:
            return []

        base_meta = metadata or {}
        chunks: List[DocumentChunkResult] = []
        step = self._chunk_size - self._chunk_overlap
        start = 0

        while start < len(text):
            end = start + self._chunk_size
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(DocumentChunkResult(
                    chunk_id=str(uuid.uuid4()),
                    text=chunk_text,
                    chunk_index=len(chunks),
                    total_chunks=0,  # filled below
                    metadata={**base_meta, "start_char": start, "end_char": end},
                ))
            start += step

        # Backfill total_chunks
        total = len(chunks)
        for c in chunks:
            c.total_chunks = total

        logger.debug("Text chunked", total_chunks=total, chunk_size=self._chunk_size)
        return chunks

    def chunk_documents(
        self,
        documents: List[Dict[str, Any]],
        text_field: str = "text",
    ) -> List[DocumentChunkResult]:
        """Chunk a list of document dicts, preserving per-document metadata."""
        all_chunks: List[DocumentChunkResult] = []
        for doc in documents:
            text = doc.get(text_field, "")
            meta = {k: v for k, v in doc.items() if k != text_field}
            all_chunks.extend(self.chunk_text(text, metadata=meta))
        return all_chunks
