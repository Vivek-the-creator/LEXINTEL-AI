import uuid
import time
import re
from typing import Optional, AsyncIterator, List
from datetime import datetime

from langgraph.graph import StateGraph, END

from app.ai.orchestrator.state import LexIntelState, create_initial_state
from app.ai.agents.placeholder_agent import PlaceholderAgent
from app.ai.logging.logger import AILogger

logger = AILogger("orchestrator")


# ── Shared utility nodes ──────────────────────────────────────────────────────

async def input_sanitizer_node(state: LexIntelState) -> LexIntelState:
    logger.node_enter("input_sanitizer", state["session_id"])
    start = time.perf_counter()
    raw = state.get("raw_input") or ""
    sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", raw.strip())[:32_000]
    state["sanitized_input"] = sanitized
    logger.node_exit("input_sanitizer", state["session_id"], (time.perf_counter() - start) * 1000)
    return state


async def output_formatter_node(state: LexIntelState) -> LexIntelState:
    logger.node_enter("output_formatter", state["session_id"])
    state["updated_at"] = datetime.utcnow().isoformat()
    state["metadata"] = {
        **state.get("metadata", {}),
        "pipeline_completed": True,
        "completed_at": datetime.utcnow().isoformat(),
    }
    logger.node_exit("output_formatter", state["session_id"], 0)
    return state


# ── Phase 2 — Placeholder node ────────────────────────────────────────────────

async def placeholder_agent_node(state: LexIntelState) -> LexIntelState:
    logger.node_enter("placeholder_agent", state["session_id"])
    start = time.perf_counter()
    state = await PlaceholderAgent().run(state)
    logger.node_exit("placeholder_agent", state["session_id"], (time.perf_counter() - start) * 1000)
    return state


# ── Phase 3A — Agent nodes ────────────────────────────────────────────────────

async def document_intelligence_node(state: LexIntelState) -> LexIntelState:
    logger.node_enter("doc_intel_node", state["session_id"])
    start = time.perf_counter()
    from app.ai.agents.document_intelligence import DocumentIntelligenceAgent
    state = await DocumentIntelligenceAgent().run(state)
    logger.node_exit("doc_intel_node", state["session_id"], (time.perf_counter() - start) * 1000)
    return state


async def legal_research_node(state: LexIntelState) -> LexIntelState:
    logger.node_enter("legal_research_node", state["session_id"])
    start = time.perf_counter()
    from app.ai.agents.legal_research import LegalResearchAgent
    state = await LegalResearchAgent().run(state)
    logger.node_exit("legal_research_node", state["session_id"], (time.perf_counter() - start) * 1000)
    return state


async def similar_cases_node(state: LexIntelState) -> LexIntelState:
    logger.node_enter("similar_cases_node", state["session_id"])
    start = time.perf_counter()
    from app.ai.agents.similar_cases import SimilarCaseRetrievalAgent
    state = await SimilarCaseRetrievalAgent().run(state)
    logger.node_exit("similar_cases_node", state["session_id"], (time.perf_counter() - start) * 1000)
    return state


async def evidence_analysis_node(state: LexIntelState) -> LexIntelState:
    logger.node_enter("evidence_node", state["session_id"])
    start = time.perf_counter()
    from app.ai.agents.evidence_analysis import EvidenceAnalysisAgent
    state = await EvidenceAnalysisAgent().run(state)
    logger.node_exit("evidence_node", state["session_id"], (time.perf_counter() - start) * 1000)
    return state


# ── Phase 3B — Agent nodes ────────────────────────────────────────────────────

async def outcome_prediction_node(state: LexIntelState) -> LexIntelState:
    logger.node_enter("outcome_prediction_node", state["session_id"])
    start = time.perf_counter()
    from app.ai.agents.outcome_prediction import OutcomePredictionAgent
    state = await OutcomePredictionAgent().run(state)
    logger.node_exit("outcome_prediction_node", state["session_id"], (time.perf_counter() - start) * 1000)
    return state


async def strategy_planning_node(state: LexIntelState) -> LexIntelState:
    logger.node_enter("strategy_planning_node", state["session_id"])
    start = time.perf_counter()
    from app.ai.agents.strategy_planning import StrategyPlanningAgent
    state = await StrategyPlanningAgent().run(state)
    logger.node_exit("strategy_planning_node", state["session_id"], (time.perf_counter() - start) * 1000)
    return state


async def legal_drafting_node(state: LexIntelState) -> LexIntelState:
    logger.node_enter("legal_drafting_node", state["session_id"])
    start = time.perf_counter()
    from app.ai.agents.legal_drafting import LegalDraftingAgent
    state = await LegalDraftingAgent().run(state)
    logger.node_exit("legal_drafting_node", state["session_id"], (time.perf_counter() - start) * 1000)
    return state


async def report_explainability_node(state: LexIntelState) -> LexIntelState:
    logger.node_enter("report_explainability_node", state["session_id"])
    start = time.perf_counter()
    from app.ai.agents.report_explainability import ReportExplainabilityAgent
    state = await ReportExplainabilityAgent().run(state)
    logger.node_exit("report_explainability_node", state["session_id"], (time.perf_counter() - start) * 1000)
    return state


# ── Routing ───────────────────────────────────────────────────────────────────

def route_after_sanitizer(state: LexIntelState) -> str:
    pipeline = state.get("pipeline_name", "placeholder")
    if pipeline in ("phase3a", "phase3b"):
        return "doc_intel_node"
    return "placeholder_agent"


def route_after_evidence(state: LexIntelState) -> str:
    """Continue to Phase 3B agents or stop at output_formatter."""
    if state.get("pipeline_name") == "phase3b":
        return "outcome_prediction_node"
    return "output_formatter"


# ── Graph builder ─────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(LexIntelState)

    # Shared nodes
    graph.add_node("input_sanitizer", input_sanitizer_node)
    graph.add_node("output_formatter", output_formatter_node)
    graph.add_node("placeholder_agent", placeholder_agent_node)

    # Phase 3A nodes
    graph.add_node("doc_intel_node", document_intelligence_node)
    graph.add_node("legal_research_node", legal_research_node)
    graph.add_node("similar_cases_node", similar_cases_node)
    graph.add_node("evidence_node", evidence_analysis_node)

    # Phase 3B nodes
    graph.add_node("outcome_prediction_node", outcome_prediction_node)
    graph.add_node("strategy_planning_node", strategy_planning_node)
    graph.add_node("legal_drafting_node", legal_drafting_node)
    graph.add_node("report_explainability_node", report_explainability_node)

    graph.set_entry_point("input_sanitizer")

    graph.add_conditional_edges(
        "input_sanitizer",
        route_after_sanitizer,
        {
            "placeholder_agent": "placeholder_agent",
            "doc_intel_node": "doc_intel_node",
        },
    )

    # Phase 2 path
    graph.add_edge("placeholder_agent", "output_formatter")

    # Phase 3A sequential path
    graph.add_edge("doc_intel_node", "legal_research_node")
    graph.add_edge("legal_research_node", "similar_cases_node")
    graph.add_edge("similar_cases_node", "evidence_node")

    # After evidence: branch to Phase 3B or finish
    graph.add_conditional_edges(
        "evidence_node",
        route_after_evidence,
        {
            "outcome_prediction_node": "outcome_prediction_node",
            "output_formatter": "output_formatter",
        },
    )

    # Phase 3B sequential path
    graph.add_edge("outcome_prediction_node", "strategy_planning_node")
    graph.add_edge("strategy_planning_node", "legal_drafting_node")
    graph.add_edge("legal_drafting_node", "report_explainability_node")
    graph.add_edge("report_explainability_node", "output_formatter")

    graph.add_edge("output_formatter", END)
    return graph


# ── Compiled graph singleton ──────────────────────────────────────────────────

_compiled_graph = None


def get_compiled_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph().compile()
    return _compiled_graph


# ── Public orchestrator API ───────────────────────────────────────────────────

class LexIntelOrchestrator:
    """High-level interface for executing AI pipelines."""

    def __init__(self):
        self._graph = get_compiled_graph()
        self._logger = AILogger("orchestrator")

    async def run(
        self,
        raw_input: str,
        pipeline_name: str = "placeholder",
        user_id: Optional[str] = None,
        case_id: Optional[str] = None,
        session_id: Optional[str] = None,
        uploaded_file_paths: Optional[List[str]] = None,
        uploaded_file_ids: Optional[List[str]] = None,
    ) -> LexIntelState:
        sid = session_id or str(uuid.uuid4())
        state = create_initial_state(
            session_id=sid,
            pipeline_name=pipeline_name,
            raw_input=raw_input,
            user_id=user_id,
            case_id=case_id,
            uploaded_file_paths=uploaded_file_paths or [],
            uploaded_file_ids=uploaded_file_ids or [],
        )
        self._logger.info("Pipeline started", pipeline=pipeline_name, session_id=sid)
        result: LexIntelState = await self._graph.ainvoke(state)
        self._logger.info(
            "Pipeline completed",
            pipeline=pipeline_name,
            session_id=sid,
            errors=len(result.get("errors", [])),
        )
        return result

    async def stream(
        self,
        raw_input: str,
        pipeline_name: str = "placeholder",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AsyncIterator[str]:
        from app.ai.llm.service import get_llm_provider
        from app.ai.prompts.registry import prompt_registry

        sid = session_id or str(uuid.uuid4())
        llm = get_llm_provider()
        prompt = prompt_registry.get("placeholder_summarizer")
        sanitized = raw_input.strip()[:32_000]
        self._logger.info("Streaming started", session_id=sid)
        async for chunk in llm.stream(prompt.system, prompt.render_user(text=sanitized)):
            yield chunk
