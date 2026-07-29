"""Tests for SimilarCaseRetrievalAgent."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


MOCK_CASES_RESPONSE = '''[
    {
        "case_name": "State of Maharashtra vs Ramesh Kumar",
        "citation": "AIR 2020 SC 1234",
        "court": "Supreme Court of India",
        "year": "2020",
        "summary": "Conviction upheld for murder under Section 302 IPC.",
        "verdict": "Convicted",
        "key_principles": ["Circumstantial evidence sufficient for conviction", "Last seen theory"]
    }
]'''

MOCK_FAISS_RESULTS = [
    {
        "score": 0.82,
        "chunk_id": "chunk-001",
        "text": "State of Maharashtra vs Ramesh Kumar AIR 2020 SC 1234. Accused convicted under Section 302 IPC.",
    }
]


@pytest.mark.asyncio
async def test_similar_cases_with_results(state_with_doc_intel):
    from app.ai.agents.similar_cases import SimilarCaseRetrievalAgent

    mock_response = MagicMock()
    mock_response.content = MOCK_CASES_RESPONSE
    mock_response.model = "llama-3.1-8b-instant"
    mock_response.total_tokens = 120

    with patch.object(SimilarCaseRetrievalAgent, "invoke_llm", new=AsyncMock(return_value=mock_response)):
        with patch.object(SimilarCaseRetrievalAgent, "_search_cases", return_value=MOCK_FAISS_RESULTS):
            result = await SimilarCaseRetrievalAgent().run(state_with_doc_intel)

    assert len(result["similar_cases"]) == 1
    case = result["similar_cases"][0]
    assert case["case_name"] == "State of Maharashtra vs Ramesh Kumar"
    assert case["citation"] == "AIR 2020 SC 1234"
    assert case["similarity_score"] == 0.82
    assert case["verdict"] == "Convicted"
    assert result["errors"] == []


@pytest.mark.asyncio
async def test_similar_cases_empty_index(base_state):
    from app.ai.agents.similar_cases import SimilarCaseRetrievalAgent

    with patch.object(SimilarCaseRetrievalAgent, "_search_cases", return_value=[]):
        result = await SimilarCaseRetrievalAgent().run(base_state)

    assert result["similar_cases"] == []
    assert any("no similar cases" in w for w in result["warnings"])
    assert result["errors"] == []


@pytest.mark.asyncio
async def test_similar_cases_empty_query(base_state):
    from app.ai.agents.similar_cases import SimilarCaseRetrievalAgent

    base_state["raw_input"] = ""
    base_state["sanitized_input"] = ""

    result = await SimilarCaseRetrievalAgent().run(base_state)

    assert result["similar_cases"] == []
    assert any("no query" in w for w in result["warnings"])


@pytest.mark.asyncio
async def test_similar_cases_sorted_by_score(state_with_doc_intel):
    from app.ai.agents.similar_cases import SimilarCaseRetrievalAgent

    faiss_results = [
        {"score": 0.65, "chunk_id": "c1", "text": "Case A text"},
        {"score": 0.91, "chunk_id": "c2", "text": "Case B text"},
        {"score": 0.78, "chunk_id": "c3", "text": "Case C text"},
    ]
    mock_response = MagicMock()
    mock_response.content = '''[
        {"case_name": "Case A", "citation": "", "court": "HC", "year": "2019",
         "summary": "s", "verdict": "Dismissed", "key_principles": []},
        {"case_name": "Case B", "citation": "", "court": "SC", "year": "2021",
         "summary": "s", "verdict": "Allowed", "key_principles": []},
        {"case_name": "Case C", "citation": "", "court": "DC", "year": "2020",
         "summary": "s", "verdict": "Convicted", "key_principles": []}
    ]'''
    mock_response.model = "llama-3.1-8b-instant"
    mock_response.total_tokens = 100

    with patch.object(SimilarCaseRetrievalAgent, "invoke_llm", new=AsyncMock(return_value=mock_response)):
        with patch.object(SimilarCaseRetrievalAgent, "_search_cases", return_value=faiss_results):
            result = await SimilarCaseRetrievalAgent().run(state_with_doc_intel)

    scores = [c["similarity_score"] for c in result["similar_cases"]]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_similar_cases_raw_text_query(base_state):
    from app.ai.agents.similar_cases import SimilarCaseRetrievalAgent

    base_state["sanitized_input"] = "Murder case under Section 302 IPC."

    mock_response = MagicMock()
    mock_response.content = MOCK_CASES_RESPONSE
    mock_response.model = "llama-3.1-8b-instant"
    mock_response.total_tokens = 100

    with patch.object(SimilarCaseRetrievalAgent, "invoke_llm", new=AsyncMock(return_value=mock_response)):
        with patch.object(SimilarCaseRetrievalAgent, "_search_cases", return_value=MOCK_FAISS_RESULTS):
            result = await SimilarCaseRetrievalAgent().run(base_state)

    assert len(result["similar_cases"]) == 1
