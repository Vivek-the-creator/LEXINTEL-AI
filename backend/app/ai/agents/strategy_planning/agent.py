from app.ai.agents.base_agent import BaseAgent
from app.ai.orchestrator.state import LexIntelState
from app.ai.logging.logger import AILogger

logger = AILogger("agent.strategy_planning")

_DISCLAIMER = (
    "⚠️ AI DISCLAIMER: These strategies are AI-generated suggestions based on the available "
    "case information. They do not constitute legal advice. Consult a qualified lawyer to "
    "evaluate which strategy is appropriate for your specific circumstances."
)


class StrategyPlanningAgent(BaseAgent):
    """
    Phase 3B — Agent 2: Legal Strategy Planning

    Consumes Phase 3A + outcome prediction to generate multiple ranked legal strategies,
    each with pros, cons, effort estimate, risk level, and required next steps.
    """

    agent_name = "strategy_planning"
    prompt_name = "strategy_planning"

    async def execute(self, state: LexIntelState) -> LexIntelState:
        doc_intel = state.get("document_intelligence") or {}
        legal_research = state.get("legal_research") or {}
        outcome_prediction = state.get("outcome_prediction") or {}
        evidence_analysis = state.get("evidence_analysis") or {}
        missing_hints = state.get("missing_evidence_hints") or []
        similar_cases = state.get("similar_cases") or []

        _sanitized = state.get("sanitized_input") or ""
        case_summary = doc_intel.get("summary") or _sanitized
        remedies = "; ".join((legal_research.get("remedies") or [])[:6])
        applicable_acts = ", ".join(legal_research.get("applicable_acts") or [])
        prediction_summary = (
            f"Probability: {outcome_prediction.get('probability_of_success') or 'N/A'}, "
            f"Strength: {outcome_prediction.get('case_strength_score') or 'N/A'}, "
            f"Risk: {outcome_prediction.get('risk_level') or 'N/A'}"
        )
        missing_list = "; ".join(missing_hints[:5])
        similar_verdicts = "; ".join(
            f"{c.get('case_name','?')} → {c.get('verdict','?')}"
            for c in (similar_cases or [])[:4]
        )
        evidence_summary = evidence_analysis.get("analysis_summary") or ""

        prompt = self.get_prompt()
        response = await self.invoke_llm(
            prompt.system,
            prompt.render_user(
                case_summary=case_summary[:1000],
                remedies=remedies[:500],
                applicable_acts=applicable_acts[:400],
                prediction_summary=prediction_summary[:300],
                missing_list=missing_list[:300],
                similar_verdicts=similar_verdicts[:500],
                evidence_summary=evidence_summary[:500],
            ),
        )
        parsed = self.parse_json_response(response.content)

        parsed["disclaimer"] = _DISCLAIMER
        parsed["ai_generated"] = True

        state["legal_strategy"] = parsed

        logger.info(
            "Strategy planning complete",
            strategies=len(parsed.get("strategies") or []),
        )
        return state
