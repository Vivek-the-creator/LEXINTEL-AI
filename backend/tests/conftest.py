"""
Shared pytest fixtures for Phase 3A agent tests.
Run from backend/: pytest tests/ -v
"""
import os
import sys
import pytest

# Ensure the backend package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Set minimal env vars before any app imports
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest")
os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("LLM_MODEL", "openai/gpt-oss-120b")


@pytest.fixture
def base_state():
    """A clean initial LexIntelState for testing."""
    from app.ai.orchestrator.state import create_initial_state
    return create_initial_state(
        session_id="test-session-001",
        pipeline_name="phase3a",
        raw_input="The accused was arrested under Section 302 IPC for murder.",
        user_id="test-user",
        case_id="test-case-001",
    )


@pytest.fixture
def state_with_doc_intel(base_state):
    """State pre-populated with document intelligence output."""
    from app.ai.orchestrator.state import DocumentIntelligenceResult
    base_state["document_intelligence"] = DocumentIntelligenceResult(
        document_type="FIR",
        summary="FIR filed against accused for murder under Section 302 IPC at PS Connaught Place.",
        language="en",
        page_count=2,
        ocr_used=False,
        confidence=0.92,
        parties=["Ramesh Kumar", "Suresh Singh"],
        organizations=["Delhi Police", "PS Connaught Place"],
        locations=["Connaught Place", "New Delhi"],
        dates=["15/01/2024", "16/01/2024"],
        legal_sections=["Section 302 IPC", "Section 120B IPC"],
        entities=[],
        raw_text="FIR No. 001/2024. Accused Ramesh Kumar arrested for murder.",
    )
    base_state["sanitized_input"] = base_state["raw_input"]
    base_state["extracted_entities"] = {
        "parties": ["Ramesh Kumar", "Suresh Singh"],
        "legal_sections": ["Section 302 IPC"],
        "locations": ["Connaught Place"],
        "dates": ["15/01/2024"],
        "organizations": ["Delhi Police"],
    }
    return base_state
