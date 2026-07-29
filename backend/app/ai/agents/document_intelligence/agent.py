import os
from typing import List

from app.ai.agents.base_agent import BaseAgent
from app.ai.orchestrator.state import (
    LexIntelState, DocumentIntelligenceResult, ExtractedEntity, DocumentChunk
)
from app.ai.agents.document_intelligence.extractor import extract_text_from_file
from app.ai.logging.logger import AILogger

logger = AILogger("agent.document_intelligence")


class DocumentIntelligenceAgent(BaseAgent):
    """
    Phase 3A — Agent 1: Document Intelligence

    Responsibilities:
    - Extract text from PDFs (native + OCR fallback) and images
    - Detect document type
    - Extract parties, organizations, locations, dates, legal sections
    - Generate a concise summary
    - Populate state.document_intelligence and state.document_chunks
    """

    agent_name = "document_intelligence"
    prompt_name = "document_intelligence"

    async def execute(self, state: LexIntelState) -> LexIntelState:
        file_paths = state.get("uploaded_file_paths") or []

        # Also accept raw text input (for API testing without file upload)
        raw_text = self.sanitize_input(state.get("sanitized_input") or state.get("raw_input") or "")

        if not file_paths and not raw_text:
            state["warnings"] = [
                *state.get("warnings", []),
                "DocumentIntelligenceAgent: no files or text provided",
            ]
            return state

        # ── Extract text from all uploaded files ──────────────────────────────
        all_text_parts: List[str] = []
        total_pages = 0
        ocr_used = False

        for path in file_paths:
            if not os.path.exists(path):
                state["warnings"] = [
                    *state.get("warnings", []),
                    f"File not found: {path}",
                ]
                continue
            text, pages, used_ocr = extract_text_from_file(path)
            if text:
                all_text_parts.append(text)
            total_pages += pages
            if used_ocr:
                ocr_used = True

        if raw_text and not all_text_parts:
            all_text_parts.append(raw_text)

        combined_text = "\n\n".join(all_text_parts)
        if not combined_text.strip():
            state["warnings"] = [
                *state.get("warnings", []),
                "DocumentIntelligenceAgent: no text could be extracted",
            ]
            return state

        # ── Truncate for LLM (keep first 6000 chars for extraction prompt) ────
        llm_text = self.sanitize_input(combined_text)[:6000]

        # ── Call LLM for structured extraction ────────────────────────────────
        prompt = self.get_prompt()
        response = await self.invoke_llm(
            prompt.system,
            prompt.render_user(text=llm_text),
        )
        parsed = self.parse_json_response(response.content)

        # ── Build typed result ────────────────────────────────────────────────
        raw_entities = parsed.get("entities") or []
        entities: List[ExtractedEntity] = [
            ExtractedEntity(
                text=e.get("text", ""),
                label=e.get("label", "UNKNOWN"),
                confidence=float(e.get("confidence", 0.8)),
                context=e.get("context"),
            )
            for e in raw_entities
            if isinstance(e, dict) and e.get("text")
        ]

        result = DocumentIntelligenceResult(
            document_type=parsed.get("document_type", "UNKNOWN"),
            summary=parsed.get("summary", ""),
            language=parsed.get("language", "en"),
            page_count=total_pages or 1,
            ocr_used=ocr_used,
            confidence=float(parsed.get("confidence", 0.8)),
            parties=parsed.get("parties") or [],
            organizations=parsed.get("organizations") or [],
            locations=parsed.get("locations") or [],
            dates=parsed.get("dates") or [],
            legal_sections=parsed.get("legal_sections") or [],
            entities=entities,
            raw_text=combined_text[:50_000],   # cap stored raw text
        )

        # ── Chunk the full text and store in state ────────────────────────────
        from app.ai.rag.chunker import TextChunker
        chunker = TextChunker()
        chunk_results = chunker.chunk_text(
            combined_text,
            metadata={"source": "document_intelligence", "document_type": result["document_type"]},
        )
        doc_chunks: List[DocumentChunk] = [
            DocumentChunk(
                chunk_id=c.chunk_id,
                text=c.text,
                metadata=c.metadata,
                embedding=None,
            )
            for c in chunk_results
        ]

        # ── Update state ──────────────────────────────────────────────────────
        state["document_intelligence"] = result
        state["document_chunks"] = doc_chunks
        state["extracted_entities"] = {
            "parties": result["parties"],
            "organizations": result["organizations"],
            "locations": result["locations"],
            "dates": result["dates"],
            "legal_sections": result["legal_sections"],
        }
        # Build retrieval query from summary + legal sections for downstream agents
        query_parts = [result["summary"]]
        if result["legal_sections"]:
            query_parts.append(" ".join(result["legal_sections"][:3]))
        state["retrieval_query"] = " ".join(query_parts)[:500]
        state["current_response"] = result["summary"]

        logger.info(
            "Document intelligence complete",
            doc_type=result["document_type"],
            pages=result["page_count"],
            ocr=result["ocr_used"],
            entities=len(entities),
            chunks=len(doc_chunks),
        )
        return state
