"""Integration tests for the Phase 3A LangGraph pipeline and shared state."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _mock_llm(content: str) -> MagicMock:
    r = MagicMock()
    r.content = content
    r.model = "llama-3.1-8b-instant"
    r.total_tokens = 100
    return r


DOC_INTEL_JSON = '''{
    "document_type": "FIR",
    "summary": "FIR filed for murder under Section 302 IPC at Connaught Place.",
    "language": "en",
    "parties": ["Ramesh Kumar"],
    "organizations": ["Delhi Police"],
    "locations": ["Connaught Place"],
    "dates": ["15/01/2024"],
    "legal_sections": ["Section 302 IPC"],
    "entities": [],
    "confidence": 0.9
}'''

RESEARCH_JSON = '''{
    "applicable_acts": ["Indian Penal Code, 1860"],
    "provisions": [{"act": "IPC", "section": "302", "title": "Murder",
                    "description": "Punishment for murder.", "relevance_score": 0.95,
                    "plain_language": "Applies to murder charges."}],
    "remedies": ["File charge sheet"],
    "legal_principles": ["Mens rea required"],
    "research_summary": "Section 302 IPC applies."
}'''

EVIDENCE_JSON = '''{
    "timeline": [{"timestamp": "2024-01-15T22:00:00",
                  "event_description": "Incident", "evidence_ids": [], "confidence": 0.9}],
    "categories": {"documentary": [], "digital": [], "physical": [], "testimonial": []},
    "missing_evidence_hints": ["CCTV footage"],
    "analysis_summary": "One event identified."
}'''


# ── State structure tests ─────────────────────────────────────────────────────

def test_initial_state_has_phase3a_fields():
    from app.ai.orchestrator.state import create_initial_state
    state = create_initial_state("s1", "phase3a", "test input")
    assert state["document_intelligence"] is None
    assert state["legal_research"] is None
    assert state["similar_cases"] == []
    assert state["evidence_items"] == []
    assert state["evidence_timeline"] == []
    assert state["missing_evidence_hints"] == []
    assert state["uploaded_file_paths"] == []


def test_state_progressive_enrichment(state_with_doc_intel):
    from app.ai.orchestrator.state import LegalResearchResult, SimilarCase

    state = state_with_doc_intel
    assert state["document_intelligence"] is not None

    state["legal_research"] = LegalResearchResult(
        applicable_acts=["IPC"],
        provisions=[],
        remedies=[],
        legal_principles=[],
        rag_chunks_used=0,
        research_summary="IPC applies.",
    )
    # Prior agent output must not be overwritten
    assert state["document_intelligence"] is not None
    assert state["legal_research"] is not None

    state["similar_cases"] = [SimilarCase(
        case_name="Test Case", citation="AIR 2020 SC 1", court="SC",
        year="2020", similarity_score=0.85, summary="Test",
        verdict="Convicted", key_principles=[],
    )]
    assert state["document_intelligence"] is not None
    assert state["legal_research"] is not None
    assert len(state["similar_cases"]) == 1


# ── Graph routing tests ───────────────────────────────────────────────────────

def test_graph_routes_placeholder():
    from app.ai.orchestrator.graph import route_after_sanitizer
    from app.ai.orchestrator.state import create_initial_state
    state = create_initial_state("s1", "placeholder", "test")
    assert route_after_sanitizer(state) == "placeholder_agent"


def test_graph_routes_phase3a():
    from app.ai.orchestrator.graph import route_after_sanitizer
    from app.ai.orchestrator.state import create_initial_state
    state = create_initial_state("s1", "phase3a", "test")
    assert route_after_sanitizer(state) == "doc_intel_node"


def test_graph_compiles():
    from app.ai.orchestrator.graph import build_graph
    compiled = build_graph().compile()
    assert compiled is not None


# ── Full pipeline integration ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_phase3a_full_pipeline():
    from app.ai.orchestrator.graph import LexIntelOrchestrator
    from app.ai.agents.document_intelligence import DocumentIntelligenceAgent
    from app.ai.agents.legal_research import LegalResearchAgent
    from app.ai.agents.similar_cases import SimilarCaseRetrievalAgent
    from app.ai.agents.evidence_analysis import EvidenceAnalysisAgent

    with patch.object(DocumentIntelligenceAgent, "invoke_llm",
                      new=AsyncMock(return_value=_mock_llm(DOC_INTEL_JSON))):
        with patch.object(LegalResearchAgent, "invoke_llm",
                          new=AsyncMock(return_value=_mock_llm(RESEARCH_JSON))):
            with patch.object(LegalResearchAgent, "_retrieve_legal_context", return_value=""):
                with patch.object(SimilarCaseRetrievalAgent, "_search_cases", return_value=[]):
                    with patch.object(EvidenceAnalysisAgent, "invoke_llm",
                                      new=AsyncMock(return_value=_mock_llm(EVIDENCE_JSON))):
                        result = await LexIntelOrchestrator().run(
                            raw_input="FIR filed for murder under Section 302 IPC.",
                            pipeline_name="phase3a",
                        )

    agent_names = [e["agent"] for e in result["agent_executions"]]
    assert "document_intelligence" in agent_names
    assert "legal_research" in agent_names
    assert "similar_case_retrieval" in agent_names
    assert "evidence_analysis" in agent_names

    assert result["document_intelligence"]["document_type"] == "FIR"
    assert result["legal_research"]["applicable_acts"] == ["Indian Penal Code, 1860"]
    assert result["similar_cases"] == []
    assert result["metadata"]["pipeline_completed"] is True
    assert result["errors"] == []


@pytest.mark.asyncio
async def test_phase3a_agent_failure_isolation():
    """A failing agent must not crash the pipeline — error is recorded, pipeline completes."""
    from app.ai.orchestrator.graph import LexIntelOrchestrator
    from app.ai.agents.document_intelligence import DocumentIntelligenceAgent
    from app.ai.agents.legal_research import LegalResearchAgent
    from app.ai.agents.similar_cases import SimilarCaseRetrievalAgent
    from app.ai.agents.evidence_analysis import EvidenceAnalysisAgent

    with patch.object(DocumentIntelligenceAgent, "invoke_llm",
                      new=AsyncMock(side_effect=Exception("LLM timeout"))):
        with patch.object(LegalResearchAgent, "invoke_llm",
                          new=AsyncMock(return_value=_mock_llm(RESEARCH_JSON))):
            with patch.object(LegalResearchAgent, "_retrieve_legal_context", return_value=""):
                with patch.object(SimilarCaseRetrievalAgent, "_search_cases", return_value=[]):
                    with patch.object(EvidenceAnalysisAgent, "invoke_llm",
                                      new=AsyncMock(return_value=_mock_llm(EVIDENCE_JSON))):
                        result = await LexIntelOrchestrator().run(
                            raw_input="Test failure isolation.",
                            pipeline_name="phase3a",
                        )

    assert result["metadata"]["pipeline_completed"] is True
    assert len(result["errors"]) > 0
    assert result["errors"][0]["agent"] == "document_intelligence"
    assert result["errors"][0]["recoverable"] is True
