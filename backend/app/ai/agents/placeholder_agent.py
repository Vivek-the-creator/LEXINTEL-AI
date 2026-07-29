from app.ai.agents.base_agent import BaseAgent
from app.ai.orchestrator.state import LexIntelState


class PlaceholderAgent(BaseAgent):
    """
    Pipeline validation agent.

    Exercises the full AI infrastructure:
      raw_input → sanitize → prompt registry → LLM → JSON parse → state update

    This is NOT a legal agent. It exists only to prove the pipeline works
    before Phase 3 legal agents are built.
    """

    agent_name = "placeholder_summarizer"
    prompt_name = "placeholder_summarizer"

    async def execute(self, state: LexIntelState) -> LexIntelState:
        raw = state.get("raw_input") or ""
        text = self.sanitize_input(raw)

        if not text:
            state["current_response"] = "No input provided."
            state["warnings"] = [*state.get("warnings", []), "PlaceholderAgent received empty input"]
            return state

        state["sanitized_input"] = text

        prompt = self.get_prompt()
        system = prompt.system
        user = prompt.render_user(text=text)

        response = await self.invoke_llm(system, user)

        parsed = self.parse_json_response(response.content)
        summary = parsed.get("summary", response.content)
        key_points = parsed.get("key_points", [])

        state["current_response"] = summary
        state["metadata"] = {
            **state.get("metadata", {}),
            "placeholder_result": {
                "summary": summary,
                "key_points": key_points,
                "model": response.model,
                "total_tokens": response.total_tokens,
            },
        }
        return state
