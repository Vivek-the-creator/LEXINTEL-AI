from typing import List, Optional

from app.ai.agents.base_agent import BaseAgent
from app.ai.orchestrator.state import LexIntelState, LegalResearchResult, LegalProvision
from app.ai.logging.logger import AILogger
from app.core.config import settings

logger = AILogger("agent.legal_research")


class LegalResearchAgent(BaseAgent):
    """
    Phase 3A — Agent 2: Legal Research

    Responsibilities:
    - Build a research query from document intelligence output
    - Retrieve relevant legal provisions from the FAISS index via RAG
    - Ask the LLM to identify applicable acts, sections, remedies, and principles
    - Populate state.legal_research
    """

    agent_name = "legal_research"
    prompt_name = "legal_research"

    async def execute(self, state: LexIntelState) -> LexIntelState:
        doc_intel = state.get("document_intelligence")
        raw_input = self.sanitize_input(state.get("sanitized_input") or state.get("raw_input") or "")

        # ── Build research query ──────────────────────────────────────────────
        if doc_intel:
            facts_parts = [doc_intel.get("summary", "")]
            if doc_intel.get("legal_sections"):
                facts_parts.append("Sections: " + ", ".join(doc_intel["legal_sections"]))
            if doc_intel.get("parties"):
                facts_parts.append("Parties: " + ", ".join(doc_intel["parties"][:5]))
            facts = " ".join(facts_parts)
            document_type = doc_intel.get("document_type", "UNKNOWN")
            parties_str = ", ".join(doc_intel.get("parties", [])[:5])
            legal_sections_str = ", ".join(doc_intel.get("legal_sections", []))
        else:
            facts = raw_input[:2000]
            document_type = "UNKNOWN"
            parties_str = ""
            legal_sections_str = ""

        if not facts.strip():
            state["warnings"] = [
                *state.get("warnings", []),
                "LegalResearchAgent: no facts available for research",
            ]
            return state

        # ── RAG retrieval from legal provisions index ─────────────────────────
        rag_context = self._retrieve_legal_context(facts)

        # ── LLM call ─────────────────────────────────────────────────────────
        prompt = self.get_prompt()
        response = await self.invoke_llm(
            prompt.system,
            prompt.render_user(
                facts=facts[:3000],
                document_type=document_type,
                parties=parties_str,
                legal_sections=legal_sections_str,
                rag_context=rag_context[:3000] if rag_context else "No indexed legal provisions available.",
            ),
        )
        parsed = self.parse_json_response(response.content)

        # ── Build typed result ────────────────────────────────────────────────
        raw_provisions = parsed.get("provisions") or []
        provisions: List[LegalProvision] = [
            LegalProvision(
                act=p.get("act", ""),
                section=p.get("section", ""),
                title=p.get("title", ""),
                description=p.get("description", ""),
                relevance_score=float(p.get("relevance_score", 0.8)),
                plain_language=p.get("plain_language", ""),
            )
            for p in raw_provisions
            if isinstance(p, dict)
        ]

        result = LegalResearchResult(
            applicable_acts=parsed.get("applicable_acts") or [],
            provisions=provisions,
            remedies=parsed.get("remedies") or [],
            legal_principles=parsed.get("legal_principles") or [],
            rag_chunks_used=rag_context.count("[") if rag_context else 0,
            research_summary=parsed.get("research_summary", ""),
        )

        state["legal_research"] = result
        state["research_results"] = [
            {"act": p["act"], "section": p["section"], "plain_language": p["plain_language"]}
            for p in provisions
        ]

        logger.info(
            "Legal research complete",
            acts=len(result["applicable_acts"]),
            provisions=len(provisions),
            remedies=len(result["remedies"]),
        )
        return state

    def _retrieve_legal_context(self, query: str) -> str:
        """Retrieve from the legal provisions FAISS index."""
        try:
            from app.ai.rag.faiss_store import FAISSVectorStore
            from app.ai.rag.embedding_service import get_embedding_service

            embedder = get_embedding_service()
            store = FAISSVectorStore(
                dimension=embedder.dimension,
                index_name=settings.LEGAL_RESEARCH_INDEX,
            )
            loaded = store.load()
            if not loaded or store.total_vectors == 0:
                logger.info("Legal provisions index empty — using LLM knowledge only")
                return ""

            query_vec = embedder.embed_text(query)
            results = store.search(
                query_vec,
                top_k=settings.LEGAL_RAG_TOP_K,
                threshold=settings.LEGAL_RAG_THRESHOLD,
            )
            if not results:
                return ""
            parts = [f"[{i+1}] {r.get('text', '')}" for i, r in enumerate(results)]
            return "\n\n".join(parts)
        except Exception as e:
            logger.warning("Legal RAG retrieval failed", error=str(e))
            return ""
