"""
Phase 3B agent tests: Outcome Prediction, Strategy Planning, Legal Drafting,
Report & Explainability, CaseState enrichment, LangGraph execution.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _mock_llm(content: str) -> MagicMock:
    r = MagicMock()
    r.content = content
    r.model = "llama-3.1-8b-instant"
    r.total_tokens = 150
    return r


# ── Fixture: fully populated Phase 3A state ──────────────────────────────────

@pytest.fixture
def phase3a_state(base_state):
    """State pre-populated with all Phase 3A outputs."""
    base_state["document_intelligence"] = {
        "document_type": "FIR",
        "summary": "FIR filed against Ramesh Kumar for murder under Section 302 IPC.",
        "language": "en",
        "page_count": 2,
        "ocr_used": False,
        "confidence": 0.92,
        "parties": ["Ramesh Kumar", "Suresh Singh"],
        "organizations": ["Delhi Police"],
        "locations": ["Connaught Place"],
        "dates": ["15/01/2024"],
        "legal_sections": ["Section 302 IPC"],
        "entities": [],
        "raw_text": "FIR No. 001/2024.",
    }
    base_state["legal_research"] = {
        "applicable_acts": ["Indian Penal Code, 1860"],
        "provisions": [{"act": "IPC", "section": "302", "title": "Murder",
                        "description": "Punishment for murder.", "relevance_score": 0.95,
                        "plain_language": "Applies to murder charges."}],
        "remedies": ["File charge sheet", "Bail application"],
        "legal_principles": ["Mens rea required"],
        "rag_chunks_used": 2,
        "research_summary": "Section 302 IPC applies to this case.",
    }
    base_state["similar_cases"] = [
        {"case_name": "State vs Sharma", "citation": "AIR 2020 SC 1", "court": "Supreme Court",
         "year": "2020", "similarity_score": 0.85, "summary": "Murder conviction upheld.",
         "verdict": "Convicted", "key_principles": ["Circumstantial evidence sufficient"]},
    ]
    base_state["evidence_items"] = [
        {"evidence_id": "e1", "file_name": "fir.pdf", "file_type": "pdf",
         "file_size_bytes": 1024, "timestamp": "2024-01-15", "extracted_timestamp": None,
         "category": "documentary", "description": "FIR document", "metadata": {},
         "is_duplicate": False, "duplicate_of": None, "hash": None},
    ]
    base_state["evidence_timeline"] = [
        {"timestamp": "2024-01-15", "event_description": "FIR filed", "evidence_ids": ["e1"], "confidence": 0.9},
    ]
    base_state["evidence_analysis"] = {
        "analysis_summary": "One documentary evidence item found.",
        "categories": {"documentary": ["e1"], "digital": [], "physical": [], "testimonial": []},
    }
    base_state["missing_evidence_hints"] = ["CCTV footage", "Witness statements"]
    base_state["sanitized_input"] = base_state["raw_input"]
    base_state["pipeline_name"] = "phase3b"
    return base_state


# ── Outcome Prediction Agent ──────────────────────────────────────────────────

PREDICTION_JSON = '''{
    "case_strength_score": 0.72,
    "probability_of_success": "72%",
    "confidence_level": "Medium",
    "confidence_reason": "Strong documentary evidence but missing CCTV.",
    "risk_level": "Medium",
    "key_strengths": ["FIR filed promptly", "Eyewitness account"],
    "key_weaknesses": ["Missing CCTV footage"],
    "counter_arguments": ["Alibi defense possible"],
    "judicial_considerations": ["Burden of proof on prosecution"],
    "missing_evidence_impact": "CCTV would strengthen the case significantly.",
    "outcome_scenarios": [
        {"scenario": "Best case", "probability": "80%", "description": "Conviction", "reasoning": "Strong evidence"},
        {"scenario": "Worst case", "probability": "20%", "description": "Acquittal", "reasoning": "Missing CCTV"}
    ],
    "evidence_used": ["FIR document"],
    "legal_references": ["Section 302 IPC"],
    "similar_judgments_influence": ["State vs Sharma — conviction upheld"]
}'''


@pytest.mark.asyncio
async def test_outcome_prediction_enriches_state(phase3a_state):
    from app.ai.agents.outcome_prediction import OutcomePredictionAgent

    with patch.object(OutcomePredictionAgent, "invoke_llm",
                      new=AsyncMock(return_value=_mock_llm(PREDICTION_JSON))):
        result = await OutcomePredictionAgent().run(phase3a_state)

    pred = result["outcome_prediction"]
    assert pred is not None
    assert pred["probability_of_success"] == "72%"
    assert pred["case_strength_score"] == 0.72
    assert pred["confidence_level"] == "Medium"
    assert pred["risk_level"] == "Medium"
    assert len(pred["key_strengths"]) == 2
    assert len(pred["key_weaknesses"]) == 1
    assert pred["ai_generated"] is True
    assert "disclaimer" in pred
    assert "AI DISCLAIMER" in pred["disclaimer"]

    # Phase 3A state must not be overwritten
    assert result["document_intelligence"] is not None
    assert result["legal_research"] is not None
    assert len(result["similar_cases"]) == 1


@pytest.mark.asyncio
async def test_outcome_prediction_handles_llm_failure(phase3a_state):
    from app.ai.agents.outcome_prediction import OutcomePredictionAgent

    with patch.object(OutcomePredictionAgent, "invoke_llm",
                      new=AsyncMock(side_effect=Exception("LLM timeout"))):
        result = await OutcomePredictionAgent().run(phase3a_state)

    # Error is recorded but pipeline continues
    assert len(result["errors"]) > 0
    assert result["errors"][0]["agent"] == "outcome_prediction"
    assert result["errors"][0]["recoverable"] is True
    # Prior state preserved
    assert result["document_intelligence"] is not None


# ── Strategy Planning Agent ───────────────────────────────────────────────────

STRATEGY_JSON = '''{
    "immediate_next_steps": ["Consult a criminal lawyer immediately", "Gather witness statements"],
    "important_deadlines": ["Bail application within 24 hours"],
    "required_additional_evidence": ["CCTV footage", "Post-mortem report"],
    "suggested_documentation": ["Affidavit of innocence"],
    "strategies": [
        {
            "name": "Strategy A — Bail Application",
            "description": "Apply for bail immediately.",
            "recommended_actions": ["File bail application", "Arrange surety"],
            "pros": ["Immediate relief", "Time to prepare defense"],
            "cons": ["May be denied in murder cases"],
            "effort": "Medium",
            "risk_level": "Medium",
            "estimated_timeline": "1-2 weeks",
            "legal_basis": ["Section 437 CrPC"]
        }
    ],
    "negotiation_possibilities": ["Plea bargain if evidence is strong"],
    "settlement_recommendations": ["Not applicable in criminal cases"],
    "escalation_options": ["High Court bail if Sessions Court denies"],
    "potential_legal_risks": ["Conviction if CCTV found"]
}'''


@pytest.mark.asyncio
async def test_strategy_planning_enriches_state(phase3a_state):
    from app.ai.agents.outcome_prediction import OutcomePredictionAgent
    from app.ai.agents.strategy_planning import StrategyPlanningAgent

    with patch.object(OutcomePredictionAgent, "invoke_llm",
                      new=AsyncMock(return_value=_mock_llm(PREDICTION_JSON))):
        phase3a_state = await OutcomePredictionAgent().run(phase3a_state)

    with patch.object(StrategyPlanningAgent, "invoke_llm",
                      new=AsyncMock(return_value=_mock_llm(STRATEGY_JSON))):
        result = await StrategyPlanningAgent().run(phase3a_state)

    strat = result["legal_strategy"]
    assert strat is not None
    assert len(strat["strategies"]) == 1
    assert strat["strategies"][0]["name"] == "Strategy A — Bail Application"
    assert len(strat["immediate_next_steps"]) == 2
    assert strat["ai_generated"] is True
    assert "disclaimer" in strat

    # Prior state preserved
    assert result["outcome_prediction"] is not None
    assert result["document_intelligence"] is not None


# ── Legal Drafting Agent ──────────────────────────────────────────────────────

DRAFT_JSON = '''{
    "document_type": "Legal Notice",
    "title": "Legal Notice to Accused",
    "content": "LEGAL NOTICE\\n\\nTo: [PLACEHOLDER: Accused Name]\\n\\nThis is to inform you...",
    "placeholders": ["Accused Name", "Date of Incident"],
    "applicable_laws_cited": ["Section 302 IPC"],
    "filing_instructions": "Send via registered post to accused's last known address.",
    "lawyer_review_notes": ["Verify accused address", "Confirm section numbers"]
}'''


@pytest.mark.asyncio
async def test_legal_drafting_generates_drafts(phase3a_state):
    from app.ai.agents.legal_drafting import LegalDraftingAgent

    with patch.object(LegalDraftingAgent, "invoke_llm",
                      new=AsyncMock(return_value=_mock_llm(DRAFT_JSON))):
        result = await LegalDraftingAgent().run(phase3a_state)

    drafts = result["legal_drafts"]
    assert len(drafts) > 0
    draft = drafts[0]
    assert draft["ai_generated"] is True
    assert draft["requires_lawyer_review"] is True
    assert "AI GENERATED DRAFT" in draft["content"]
    assert "[PLACEHOLDER" in draft["content"] or "PLACEHOLDER" in str(draft.get("placeholders", []))

    # Prior state preserved
    assert result["document_intelligence"] is not None
    assert result["legal_research"] is not None


@pytest.mark.asyncio
async def test_legal_drafting_handles_partial_failure(phase3a_state):
    """If one draft fails, others should still be generated."""
    from app.ai.agents.legal_drafting import LegalDraftingAgent

    call_count = 0

    async def flaky_llm(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("LLM error on first draft")
        return _mock_llm(DRAFT_JSON)

    with patch.object(LegalDraftingAgent, "invoke_llm", new=flaky_llm):
        result = await LegalDraftingAgent().run(phase3a_state)

    drafts = result["legal_drafts"]
    assert len(drafts) > 0
    # First draft should have error field
    assert "error" in drafts[0] or drafts[0].get("ai_generated") is True


# ── Report & Explainability Agent ─────────────────────────────────────────────

REPORT_JSON = '''{
    "executive_summary": "This is a murder case with strong documentary evidence.",
    "case_overview": {"type": "Criminal", "jurisdiction": "Delhi", "key_issue": "Murder under Section 302 IPC"},
    "entities_summary": {"parties": ["Ramesh Kumar"], "organizations": ["Delhi Police"], "locations": ["Connaught Place"]},
    "evidence_inventory": [
        {"item": "FIR document", "type": "documentary", "significance": "Primary evidence", "status": "present"},
        {"item": "CCTV footage", "type": "digital", "significance": "Corroborating evidence", "status": "missing"}
    ],
    "applicable_laws_summary": [{"act": "IPC Section 302", "relevance": "Primary charge"}],
    "similar_judgments_summary": [{"case": "State vs Sharma", "influence": "Conviction precedent"}],
    "outcome_analysis": {"prediction": "Likely conviction", "confidence": "Medium", "reasoning": "Strong FIR evidence"},
    "strategy_recommendations": [{"strategy": "Bail Application", "rationale": "Immediate relief"}],
    "legal_risks": ["Conviction if CCTV found"],
    "missing_evidence_impact": "CCTV would significantly strengthen prosecution.",
    "recommendations": ["Consult criminal lawyer immediately", "Gather witness statements"],
    "explainability": [
        {
            "conclusion": "High probability of conviction",
            "evidence_used": ["FIR document"],
            "legal_references": ["Section 302 IPC"],
            "similar_judgments": ["State vs Sharma"],
            "reasoning_chain": "FIR filed promptly. Eyewitness present. Similar case convicted.",
            "confidence_score": 0.72
        }
    ],
    "ai_confidence_overall": 0.72,
    "report_for_audience": "lawyer"
}'''


@pytest.mark.asyncio
async def test_report_explainability_generates_report(phase3a_state):
    from app.ai.agents.report_explainability import ReportExplainabilityAgent

    with patch.object(ReportExplainabilityAgent, "invoke_llm",
                      new=AsyncMock(return_value=_mock_llm(REPORT_JSON))):
        result = await ReportExplainabilityAgent().run(phase3a_state)

    report = result["case_report"]
    assert report is not None
    assert report["ai_generated"] is True
    assert "disclaimer" in report
    assert "AI GENERATED REPORT" in report["disclaimer"]
    assert report["executive_summary"] == "This is a murder case with strong documentary evidence."
    assert len(report["explainability"]) == 1
    assert report["explainability"][0]["confidence_score"] == 0.72
    assert report["ai_confidence_overall"] == 0.72

    # Full structured data attached
    assert "full_timeline" in report
    assert "full_similar_cases" in report
    assert "full_evidence_items" in report

    # Legacy field synced
    assert result["final_report"] == report["executive_summary"]

    # Prior state preserved
    assert result["document_intelligence"] is not None
    assert result["legal_research"] is not None


@pytest.mark.asyncio
async def test_report_explainability_includes_all_prior_outputs(phase3a_state):
    """Report agent must consume and reference all prior agent outputs."""
    from app.ai.agents.outcome_prediction import OutcomePredictionAgent
    from app.ai.agents.strategy_planning import StrategyPlanningAgent
    from app.ai.agents.legal_drafting import LegalDraftingAgent
    from app.ai.agents.report_explainability import ReportExplainabilityAgent

    with patch.object(OutcomePredictionAgent, "invoke_llm",
                      new=AsyncMock(return_value=_mock_llm(PREDICTION_JSON))):
        phase3a_state = await OutcomePredictionAgent().run(phase3a_state)

    with patch.object(StrategyPlanningAgent, "invoke_llm",
                      new=AsyncMock(return_value=_mock_llm(STRATEGY_JSON))):
        phase3a_state = await StrategyPlanningAgent().run(phase3a_state)

    with patch.object(LegalDraftingAgent, "invoke_llm",
                      new=AsyncMock(return_value=_mock_llm(DRAFT_JSON))):
        phase3a_state = await LegalDraftingAgent().run(phase3a_state)

    with patch.object(ReportExplainabilityAgent, "invoke_llm",
                      new=AsyncMock(return_value=_mock_llm(REPORT_JSON))):
        result = await ReportExplainabilityAgent().run(phase3a_state)

    # All Phase 3A + 3B outputs must still be present
    assert result["document_intelligence"] is not None
    assert result["legal_research"] is not None
    assert result["outcome_prediction"] is not None
    assert result["legal_strategy"] is not None
    assert len(result["legal_drafts"]) > 0
    assert result["case_report"] is not None


# ── CaseState enrichment — no overwrite guarantee ────────────────────────────

@pytest.mark.asyncio
async def test_phase3b_agents_never_overwrite_phase3a(phase3a_state):
    """Each Phase 3B agent must only ADD to state, never overwrite Phase 3A fields."""
    from app.ai.agents.outcome_prediction import OutcomePredictionAgent
    from app.ai.agents.strategy_planning import StrategyPlanningAgent
    from app.ai.agents.legal_drafting import LegalDraftingAgent
    from app.ai.agents.report_explainability import ReportExplainabilityAgent

    original_doc_intel = phase3a_state["document_intelligence"].copy()
    original_legal_research = phase3a_state["legal_research"].copy()
    original_similar_cases = list(phase3a_state["similar_cases"])
    original_evidence_items = list(phase3a_state["evidence_items"])

    state = phase3a_state
    for AgentClass, json_resp in [
        (OutcomePredictionAgent, PREDICTION_JSON),
        (StrategyPlanningAgent, STRATEGY_JSON),
        (LegalDraftingAgent, DRAFT_JSON),
        (ReportExplainabilityAgent, REPORT_JSON),
    ]:
        with patch.object(AgentClass, "invoke_llm",
                          new=AsyncMock(return_value=_mock_llm(json_resp))):
            state = await AgentClass().run(state)

        assert state["document_intelligence"] == original_doc_intel
        assert state["legal_research"] == original_legal_research
        assert state["similar_cases"] == original_similar_cases
        assert state["evidence_items"] == original_evidence_items


# ── LangGraph Phase 3B pipeline integration ───────────────────────────────────

DOC_INTEL_JSON = '''{
    "document_type": "FIR", "summary": "FIR for murder.", "language": "en",
    "parties": ["Ramesh Kumar"], "organizations": ["Delhi Police"],
    "locations": ["Delhi"], "dates": ["15/01/2024"],
    "legal_sections": ["Section 302 IPC"], "entities": [], "confidence": 0.9
}'''

RESEARCH_JSON = '''{
    "applicable_acts": ["IPC"], "provisions": [],
    "remedies": ["File charge sheet"], "legal_principles": ["Mens rea"],
    "research_summary": "IPC applies.", "rag_chunks_used": 0
}'''

EVIDENCE_JSON = '''{
    "timeline": [{"timestamp": "2024-01-15", "event_description": "FIR filed",
                  "evidence_ids": [], "confidence": 0.9}],
    "categories": {"documentary": [], "digital": [], "physical": [], "testimonial": []},
    "evidence_present": [], "missing_evidence_hints": ["CCTV"],
    "analysis_summary": "One event."
}'''


@pytest.mark.asyncio
async def test_phase3b_full_pipeline_via_langgraph():
    from app.ai.orchestrator.graph import LexIntelOrchestrator
    from app.ai.agents.document_intelligence import DocumentIntelligenceAgent
    from app.ai.agents.legal_research import LegalResearchAgent
    from app.ai.agents.similar_cases import SimilarCaseRetrievalAgent
    from app.ai.agents.evidence_analysis import EvidenceAnalysisAgent
    from app.ai.agents.outcome_prediction import OutcomePredictionAgent
    from app.ai.agents.strategy_planning import StrategyPlanningAgent
    from app.ai.agents.legal_drafting import LegalDraftingAgent
    from app.ai.agents.report_explainability import ReportExplainabilityAgent

    with patch.object(DocumentIntelligenceAgent, "invoke_llm",
                      new=AsyncMock(return_value=_mock_llm(DOC_INTEL_JSON))):
        with patch.object(LegalResearchAgent, "invoke_llm",
                          new=AsyncMock(return_value=_mock_llm(RESEARCH_JSON))):
            with patch.object(LegalResearchAgent, "_retrieve_legal_context", return_value=""):
                with patch.object(SimilarCaseRetrievalAgent, "_search_cases", return_value=[]):
                    with patch.object(EvidenceAnalysisAgent, "invoke_llm",
                                      new=AsyncMock(return_value=_mock_llm(EVIDENCE_JSON))):
                        with patch.object(OutcomePredictionAgent, "invoke_llm",
                                          new=AsyncMock(return_value=_mock_llm(PREDICTION_JSON))):
                            with patch.object(StrategyPlanningAgent, "invoke_llm",
                                              new=AsyncMock(return_value=_mock_llm(STRATEGY_JSON))):
                                with patch.object(LegalDraftingAgent, "invoke_llm",
                                                  new=AsyncMock(return_value=_mock_llm(DRAFT_JSON))):
                                    with patch.object(ReportExplainabilityAgent, "invoke_llm",
                                                      new=AsyncMock(return_value=_mock_llm(REPORT_JSON))):
                                        result = await LexIntelOrchestrator().run(
                                            raw_input="FIR filed for murder under Section 302 IPC.",
                                            pipeline_name="phase3b",
                                        )

    agent_names = [e["agent"] for e in result["agent_executions"]]
    assert "document_intelligence" in agent_names
    assert "legal_research" in agent_names
    assert "outcome_prediction" in agent_names
    assert "strategy_planning" in agent_names
    assert "legal_drafting" in agent_names
    assert "report_explainability" in agent_names

    assert result["document_intelligence"]["document_type"] == "FIR"
    assert result["outcome_prediction"]["probability_of_success"] == "72%"
    assert result["legal_strategy"] is not None
    assert len(result["legal_drafts"]) > 0
    assert result["case_report"] is not None
    assert result["metadata"]["pipeline_completed"] is True
    assert result["errors"] == []


@pytest.mark.asyncio
async def test_phase3b_routes_correctly_from_evidence():
    """After evidence analysis, pipeline must route to outcome_prediction for phase3b."""
    from app.ai.orchestrator.graph import route_after_evidence
    from app.ai.orchestrator.state import create_initial_state

    state_3b = create_initial_state("s1", "phase3b", "test")
    assert route_after_evidence(state_3b) == "outcome_prediction_node"

    state_3a = create_initial_state("s1", "phase3a", "test")
    assert route_after_evidence(state_3a) == "output_formatter"


# ── Prompt registry ───────────────────────────────────────────────────────────

def test_phase3b_prompts_registered():
    from app.ai.prompts.registry import prompt_registry
    for name in ["outcome_prediction", "strategy_planning", "legal_drafting", "report_explainability"]:
        prompt = prompt_registry.get(name)
        assert prompt.name == name
        assert prompt.system
        assert prompt.user_template
        assert "phase3b" in prompt.tags


def test_prompts_render_without_error():
    from app.ai.prompts.registry import prompt_registry

    p = prompt_registry.get("outcome_prediction")
    rendered = p.render_user(
        case_summary="Test case", legal_summary="IPC applies",
        applicable_acts="IPC", remedies="File complaint",
        similar_verdicts="Case A → Convicted", evidence_summary="One FIR",
        evidence_count="1", missing_count="1", missing_list="CCTV",
        timeline_summary="FIR filed on 15/01/2024",
    )
    assert "Test case" in rendered

    p2 = prompt_registry.get("legal_drafting")
    rendered2 = p2.render_user(
        document_type="Legal Notice", case_summary="Test",
        parties="A, B", organizations="Delhi Police", dates="15/01/2024",
        applicable_acts="IPC", legal_sections="302", remedies="Complaint",
        evidence_summary="FIR present",
    )
    assert "Legal Notice" in rendered2
