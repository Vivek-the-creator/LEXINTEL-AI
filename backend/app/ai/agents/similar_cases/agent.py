from typing import List

from app.ai.agents.base_agent import BaseAgent
from app.ai.orchestrator.state import LexIntelState, SimilarCase
from app.ai.logging.logger import AILogger
from app.core.config import settings

logger = AILogger("agent.similar_cases")


class SimilarCaseRetrievalAgent(BaseAgent):
    """
    Phase 3A — Agent 3: Similar Case Retrieval

    Responsibilities:
    - Build a semantic search query from document intelligence output
    - Search the case judgments FAISS index
    - Enrich raw chunks with structured case metadata via LLM
    - Populate state.similar_cases with ranked, structured results
    """

    agent_name = "similar_case_retrieval"
    prompt_name = "similar_case_enrichment"

    async def execute(self, state: LexIntelState) -> LexIntelState:
        doc_intel = state.get("document_intelligence")
        raw_input = self.sanitize_input(state.get("sanitized_input") or state.get("raw_input") or "")

        # ── Build search query ────────────────────────────────────────────────
        if doc_intel:
            query_parts = [doc_intel.get("summary", "")]
            if doc_intel.get("legal_sections"):
                query_parts.extend(doc_intel["legal_sections"][:3])
            query = " ".join(query_parts)[:500]
        else:
            query = raw_input[:500]

        if not query.strip():
            state["warnings"] = [
                *state.get("warnings", []),
                "SimilarCaseRetrievalAgent: no query available",
            ]
            return state

        # ── Semantic search ───────────────────────────────────────────────────
        raw_chunks = self._search_cases(query)

        if not raw_chunks:
            state["warnings"] = [
                *state.get("warnings", []),
                "SimilarCaseRetrievalAgent: no similar cases found in index",
            ]
            state["similar_cases"] = []
            return state

        # ── Enrich with LLM ───────────────────────────────────────────────────
        chunks_text = "\n\n---\n\n".join(
            f"[Chunk {i+1}] Score: {c.get('score', 0)}\n{c.get('text', '')}"
            for i, c in enumerate(raw_chunks)
        )

        prompt = self.get_prompt()
        response = await self.invoke_llm(
            prompt.system,
            prompt.render_user(chunks=chunks_text[:4000]),
        )
        parsed = self.parse_json_response(response.content)

        # ── Build typed results ───────────────────────────────────────────────
        cases: List[SimilarCase] = []
        raw_list = parsed if isinstance(parsed, list) else parsed.get("cases", [])

        for i, item in enumerate(raw_list):
            if not isinstance(item, dict):
                continue
            score = raw_chunks[i]["score"] if i < len(raw_chunks) else 0.5
            cases.append(SimilarCase(
                case_name=item.get("case_name", "Unknown Case"),
                citation=item.get("citation", ""),
                court=item.get("court", ""),
                year=item.get("year"),
                similarity_score=round(float(score), 4),
                summary=item.get("summary", ""),
                verdict=item.get("verdict", ""),
                key_principles=item.get("key_principles") or [],
            ))

        # Sort by similarity score descending
        cases.sort(key=lambda c: c["similarity_score"], reverse=True)
        state["similar_cases"] = cases

        logger.info("Similar case retrieval complete", cases_found=len(cases))
        return state

    def _search_cases(self, query: str) -> list:
        """Search the case judgments FAISS index."""
        try:
            from app.ai.rag.faiss_store import FAISSVectorStore
            from app.ai.rag.embedding_service import get_embedding_service

            embedder = get_embedding_service()
            store = FAISSVectorStore(
                dimension=embedder.dimension,
                index_name=settings.CASES_INDEX,
            )
            loaded = store.load()
            if not loaded or store.total_vectors == 0:
                logger.info("Case judgments index empty — no similar cases available")
                return []

            query_vec = embedder.embed_text(query)
            return store.search(
                query_vec,
                top_k=settings.CASES_RAG_TOP_K,
                threshold=settings.CASES_RAG_THRESHOLD,
            )
        except Exception as e:
            logger.warning("Case search failed", error=str(e))
            return []
