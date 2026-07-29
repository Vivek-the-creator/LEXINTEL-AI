"""Tests for DocumentIntelligenceAgent."""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── Unit: extractor utilities ─────────────────────────────────────────────────

def test_detect_file_type():
    from app.ai.agents.evidence_analysis.extractor import detect_file_type
    assert detect_file_type("doc.pdf") == "pdf"
    assert detect_file_type("photo.jpg") == "image"
    assert detect_file_type("clip.mp4") == "video"
    assert detect_file_type("audio.mp3") == "audio"
    assert detect_file_type("notes.txt") == "text"
    assert detect_file_type("unknown.xyz") == "unknown"


def test_file_hash_consistency(tmp_path):
    from app.ai.agents.document_intelligence.extractor import file_hash
    f = tmp_path / "test.txt"
    f.write_text("hello world")
    h1 = file_hash(str(f))
    h2 = file_hash(str(f))
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex


def test_extract_text_from_txt(tmp_path):
    from app.ai.agents.document_intelligence.extractor import extract_text_from_file
    f = tmp_path / "sample.txt"
    f.write_text("Section 302 IPC — Punishment for murder.")
    text, pages, ocr_used = extract_text_from_file(str(f))
    assert "Section 302" in text
    assert pages == 1
    assert ocr_used is False


# ── Unit: agent state enrichment ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_document_intelligence_empty_input(base_state):
    from app.ai.agents.document_intelligence import DocumentIntelligenceAgent

    base_state["raw_input"] = ""
    base_state["sanitized_input"] = ""
    base_state["uploaded_file_paths"] = []

    agent = DocumentIntelligenceAgent()
    result = await agent.run(base_state)

    assert result["document_intelligence"] is None
    assert any("no files or text" in w for w in result["warnings"])


@pytest.mark.asyncio
async def test_document_intelligence_with_text(base_state):
    from app.ai.agents.document_intelligence import DocumentIntelligenceAgent

    mock_response = MagicMock()
    mock_response.content = '''{
        "document_type": "FIR",
        "summary": "FIR filed for murder under Section 302 IPC.",
        "language": "en",
        "parties": ["Ramesh Kumar"],
        "organizations": ["Delhi Police"],
        "locations": ["New Delhi"],
        "dates": ["15/01/2024"],
        "legal_sections": ["Section 302 IPC"],
        "entities": [{"text": "Ramesh Kumar", "label": "PERSON", "confidence": 0.95}],
        "confidence": 0.9
    }'''
    mock_response.model = "llama-3.1-8b-instant"
    mock_response.total_tokens = 100

    with patch.object(DocumentIntelligenceAgent, "invoke_llm", new=AsyncMock(return_value=mock_response)):
        result = await DocumentIntelligenceAgent().run(base_state)

    assert result["document_intelligence"] is not None
    di = result["document_intelligence"]
    assert di["document_type"] == "FIR"
    assert "Ramesh Kumar" in di["parties"]
    assert "Section 302 IPC" in di["legal_sections"]
    assert len(di["entities"]) == 1
    assert len(result["document_chunks"]) > 0
    assert result["extracted_entities"]["parties"] == ["Ramesh Kumar"]
    assert result["retrieval_query"] is not None
    assert result["errors"] == []


@pytest.mark.asyncio
async def test_document_intelligence_missing_file(base_state):
    from app.ai.agents.document_intelligence import DocumentIntelligenceAgent

    base_state["uploaded_file_paths"] = ["/nonexistent/path/file.pdf"]
    base_state["raw_input"] = ""
    base_state["sanitized_input"] = ""

    agent = DocumentIntelligenceAgent()
    result = await agent.run(base_state)

    assert any("not found" in w or "no text" in w or "no files" in w for w in result["warnings"])


@pytest.mark.asyncio
async def test_document_intelligence_txt_file(tmp_path, base_state):
    from app.ai.agents.document_intelligence import DocumentIntelligenceAgent

    f = tmp_path / "fir.txt"
    f.write_text("FIR No. 001/2024. Accused arrested under Section 302 IPC for murder at Connaught Place.")
    base_state["uploaded_file_paths"] = [str(f)]
    base_state["raw_input"] = ""
    base_state["sanitized_input"] = ""

    mock_response = MagicMock()
    mock_response.content = '{"document_type":"FIR","summary":"FIR for murder.","language":"en","parties":[],"organizations":[],"locations":[],"dates":[],"legal_sections":["Section 302 IPC"],"entities":[],"confidence":0.85}'
    mock_response.model = "llama-3.1-8b-instant"
    mock_response.total_tokens = 80

    with patch.object(DocumentIntelligenceAgent, "invoke_llm", new=AsyncMock(return_value=mock_response)):
        result = await DocumentIntelligenceAgent().run(base_state)

    assert result["document_intelligence"]["document_type"] == "FIR"
    assert result["errors"] == []
