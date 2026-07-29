"""Tests for LegalResearchAgent."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


MOCK_RESEARCH_RESPONSE = '''{
    "applicable_acts": ["Indian Penal Code, 1860", "Code of Criminal Procedure, 1973"],
    "provisions": [
        {
            "act": "Indian Penal Code, 1860",
            "section": "302",
            "title": "Punishment for murder",
            "description": "Whoever commits murder shall be punished with death or imprisonment for life.",
            "relevance_score": 0.97,
            "plain_language": "This section applies because the accused is charged with murder."
        }
    ],
    "remedies": ["File charge sheet under Section 302 IPC", "Apply for bail under CrPC"],
    "legal_principles": ["Mens rea must be established", "Burden of proof on prosecution"],
    "research_summary": "The case involves murder charges under Section 302 IPC."
}'''


@pytest.mark.asyncio
async def test_legal_research_with_doc_intel(state_with_doc_intel):
    from app.ai.agents.legal_research import LegalResearchAgent

    mock_response = MagicMock()
    mock_response.content = MOCK_RESEARCH_RESPONSE
    mock_response.model = "llama-3.1-8b-instant"
    mock_response.total_tokens = 150

    with patch.object(LegalResearchAgent, "invoke_llm", new=AsyncMock(return_value=mock_response)):
        with patch.object(LegalResearchAgent, "_retrieve_legal_context", return_value=""):
            result = await LegalResearchAgent().run(state_with_doc_intel)

    assert result["legal_research"] is not None
    lr = result["legal_research"]
    assert "Indian Penal Code, 1860" in lr["applicable_acts"]
    assert len(lr["provisions"]) == 1
    assert lr["provisions"][0]["section"] == "302"
    assert len(lr["remedies"]) > 0
    assert len(lr["legal_principles"]) > 0
    assert result["errors"] == []


@pytest.mark.asyncio
async def test_legal_research_raw_text_fallback(base_state):
    from app.ai.agents.legal_research import LegalResearchAgent

    base_state["sanitized_input"] = "Accused committed murder under Section 302 IPC."

    mock_response = MagicMock()
    mock_response.content = MOCK_RESEARCH_RESPONSE
    mock_response.model = "llama-3.1-8b-instant"
    mock_response.total_tokens = 120

    with patch.object(LegalResearchAgent, "invoke_llm", new=AsyncMock(return_value=mock_response)):
        with patch.object(LegalResearchAgent, "_retrieve_legal_context", return_value=""):
            result = await LegalResearchAgent().run(base_state)

    assert result["legal_research"] is not None
    assert result["errors"] == []


@pytest.mark.asyncio
async def test_legal_research_empty_input(base_state):
    from app.ai.agents.legal_research import LegalResearchAgent

    base_state["raw_input"] = ""
    base_state["sanitized_input"] = ""

    result = await LegalResearchAgent().run(base_state)

    assert result["legal_research"] is None
    assert any("no facts" in w for w in result["warnings"])


@pytest.mark.asyncio
async def test_legal_research_rag_context_used(state_with_doc_intel):
    from app.ai.agents.legal_research import LegalResearchAgent

    rag_context = "[1] Section 302 IPC — Punishment for murder: death or life imprisonment."

    mock_response = MagicMock()
    mock_response.content = MOCK_RESEARCH_RESPONSE
    mock_response.model = "llama-3.1-8b-instant"
    mock_response.total_tokens = 160

    with patch.object(LegalResearchAgent, "invoke_llm", new=AsyncMock(return_value=mock_response)) as mock_llm:
        with patch.object(LegalResearchAgent, "_retrieve_legal_context", return_value=rag_context):
            result = await LegalResearchAgent().run(state_with_doc_intel)

    # Verify the RAG context was passed to the LLM
    call_args = mock_llm.call_args
    assert rag_context in call_args[0][1]  # user prompt contains rag_context
    assert result["legal_research"] is not None


@pytest.mark.asyncio
async def test_legal_research_state_research_results_populated(state_with_doc_intel):
    from app.ai.agents.legal_research import LegalResearchAgent

    mock_response = MagicMock()
    mock_response.content = MOCK_RESEARCH_RESPONSE
    mock_response.model = "llama-3.1-8b-instant"
    mock_response.total_tokens = 150

    with patch.object(LegalResearchAgent, "invoke_llm", new=AsyncMock(return_value=mock_response)):
        with patch.object(LegalResearchAgent, "_retrieve_legal_context", return_value=""):
            result = await LegalResearchAgent().run(state_with_doc_intel)

    # Legacy research_results field should also be populated
    assert len(result["research_results"]) > 0
    assert "section" in result["research_results"][0]
