"""Tests for EvidenceAnalysisAgent."""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


MOCK_TIMELINE_RESPONSE = '''{
    "timeline": [
        {
            "timestamp": "2024-01-15T22:30:00",
            "event_description": "Incident occurred at Connaught Place",
            "evidence_ids": [],
            "confidence": 0.85
        }
    ],
    "categories": {
        "documentary": [],
        "digital": [],
        "physical": [],
        "testimonial": []
    },
    "missing_evidence_hints": ["CCTV footage", "Post-mortem report"],
    "analysis_summary": "Limited evidence available. Key forensic documents missing."
}'''


# ── Unit: evidence extractor utilities ───────────────────────────────────────

def test_detect_file_type_evidence():
    from app.ai.agents.evidence_analysis.extractor import detect_file_type
    assert detect_file_type("evidence.pdf") == "pdf"
    assert detect_file_type("screenshot.png") == "image"
    assert detect_file_type("call_recording.mp3") == "audio"
    assert detect_file_type("cctv.mp4") == "video"
    assert detect_file_type("whatsapp.txt") == "text"
    assert detect_file_type("email.eml") == "email"


def test_detect_category():
    from app.ai.agents.evidence_analysis.extractor import detect_category
    assert detect_category("doc.pdf") == "documentary"
    assert detect_category("photo.jpg") == "digital"
    assert detect_category("audio.mp3") == "digital"
    assert detect_category("video.mp4") == "digital"


def test_extract_timestamp_from_filename():
    from app.ai.agents.evidence_analysis.extractor import extract_timestamp_from_filename
    assert extract_timestamp_from_filename("20240115_143022.jpg") is not None
    assert extract_timestamp_from_filename("2024-01-15T14:30.pdf") is not None
    assert extract_timestamp_from_filename("random_file.pdf") is None


def test_file_hash_duplicate_detection(tmp_path):
    from app.ai.agents.evidence_analysis.extractor import file_hash
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("same content")
    f2.write_text("same content")
    assert file_hash(str(f1)) == file_hash(str(f2))

    f3 = tmp_path / "c.txt"
    f3.write_text("different content")
    assert file_hash(str(f1)) != file_hash(str(f3))


def test_extract_file_metadata(tmp_path):
    from app.ai.agents.evidence_analysis.extractor import extract_file_metadata
    f = tmp_path / "20240115_143022_evidence.pdf"
    f.write_bytes(b"%PDF-1.4 test content")
    meta = extract_file_metadata(str(f))
    assert meta["filename"] == "20240115_143022_evidence.pdf"
    assert meta["size_bytes"] > 0
    assert meta["timestamp_from_filename"] is not None


# ── Unit: agent with no files ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_evidence_analysis_no_files(base_state):
    from app.ai.agents.evidence_analysis import EvidenceAnalysisAgent

    base_state["uploaded_file_paths"] = []
    result = await EvidenceAnalysisAgent().run(base_state)

    assert result["evidence_items"] == []
    assert result["evidence_timeline"] == []
    assert result["missing_evidence_hints"] == []
    assert any("no files" in w for w in result["warnings"])


# ── Unit: agent with real temp files ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_evidence_analysis_with_files(tmp_path, base_state):
    from app.ai.agents.evidence_analysis import EvidenceAnalysisAgent

    f1 = tmp_path / "fir.pdf"
    f2 = tmp_path / "screenshot.png"
    f1.write_bytes(b"%PDF-1.4 FIR document content")
    f2.write_bytes(b"\x89PNG\r\n\x1a\n fake png content")

    base_state["uploaded_file_paths"] = [str(f1), str(f2)]

    mock_response = MagicMock()
    mock_response.content = MOCK_TIMELINE_RESPONSE
    mock_response.model = "llama-3.1-8b-instant"
    mock_response.total_tokens = 130

    with patch.object(EvidenceAnalysisAgent, "invoke_llm", new=AsyncMock(return_value=mock_response)):
        result = await EvidenceAnalysisAgent().run(base_state)

    assert len(result["evidence_items"]) == 2
    assert result["evidence_items"][0]["file_type"] in {"pdf", "image", "unknown"}
    assert len(result["evidence_timeline"]) == 1
    assert "CCTV footage" in result["missing_evidence_hints"]
    assert result["evidence_analysis"]["total_items"] == 2
    assert result["errors"] == []


@pytest.mark.asyncio
async def test_evidence_duplicate_detection(tmp_path, base_state):
    from app.ai.agents.evidence_analysis import EvidenceAnalysisAgent

    content = b"identical file content for duplicate test"
    f1 = tmp_path / "original.pdf"
    f2 = tmp_path / "duplicate.pdf"
    f1.write_bytes(content)
    f2.write_bytes(content)

    base_state["uploaded_file_paths"] = [str(f1), str(f2)]

    mock_response = MagicMock()
    mock_response.content = MOCK_TIMELINE_RESPONSE
    mock_response.model = "llama-3.1-8b-instant"
    mock_response.total_tokens = 100

    with patch.object(EvidenceAnalysisAgent, "invoke_llm", new=AsyncMock(return_value=mock_response)):
        result = await EvidenceAnalysisAgent().run(base_state)

    items = result["evidence_items"]
    assert len(items) == 2
    duplicates = [e for e in items if e["is_duplicate"]]
    assert len(duplicates) == 1
    assert duplicates[0]["duplicate_of"] is not None


@pytest.mark.asyncio
async def test_evidence_timeline_sorted(tmp_path, base_state):
    from app.ai.agents.evidence_analysis import EvidenceAnalysisAgent

    f = tmp_path / "doc.txt"
    f.write_text("evidence document")
    base_state["uploaded_file_paths"] = [str(f)]

    mock_response = MagicMock()
    mock_response.content = '''{
        "timeline": [
            {"timestamp": "2024-01-20T10:00:00", "event_description": "Later event",
             "evidence_ids": [], "confidence": 0.8},
            {"timestamp": "2024-01-15T08:00:00", "event_description": "Earlier event",
             "evidence_ids": [], "confidence": 0.9}
        ],
        "categories": {"documentary": [], "digital": [], "physical": [], "testimonial": []},
        "missing_evidence_hints": [],
        "analysis_summary": "Two events identified."
    }'''
    mock_response.model = "llama-3.1-8b-instant"
    mock_response.total_tokens = 100

    with patch.object(EvidenceAnalysisAgent, "invoke_llm", new=AsyncMock(return_value=mock_response)):
        result = await EvidenceAnalysisAgent().run(base_state)

    timestamps = [e["timestamp"] for e in result["evidence_timeline"]]
    assert timestamps == sorted(timestamps)
