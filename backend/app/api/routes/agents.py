import uuid
import os
from typing import Optional, List, AsyncIterator
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.ai.logging.logger import AILogger
from app.ai.orchestrator.state import create_initial_state

router = APIRouter()
logger = AILogger("api.agents")


# ── Request schemas ───────────────────────────────────────────────────────────

class TextOnlyRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=32000)
    case_id: Optional[str] = None
    session_id: Optional[str] = None


class Phase3APipelineRequest(BaseModel):
    text: str = Field(default="", max_length=32000)
    file_paths: List[str] = Field(default_factory=list)
    case_id: Optional[str] = None
    session_id: Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_state(
    text: str,
    pipeline_name: str,
    user_id: str,
    case_id: Optional[str] = None,
    session_id: Optional[str] = None,
    file_paths: Optional[List[str]] = None,
):
    sid = session_id or str(uuid.uuid4())
    return create_initial_state(
        session_id=sid,
        pipeline_name=pipeline_name,
        raw_input=text,
        user_id=user_id,
        case_id=case_id,
        uploaded_file_paths=file_paths or [],
    )


def _resolve_upload_paths(file_ids: List[str]) -> List[str]:
    """Convert stored file IDs to absolute paths on disk."""
    paths = []
    for fid in file_ids:
        path = os.path.join(settings.UPLOAD_DIR, fid)
        if os.path.exists(path):
            paths.append(path)
    return paths


# ── 1. Document Intelligence Agent ───────────────────────────────────────────

@router.post("/document-intelligence/run")
async def run_document_intelligence(
    req: TextOnlyRequest,
    current_user: dict = Depends(get_current_user),
):
    """Run the Document Intelligence Agent on raw text input."""
    from app.ai.agents.document_intelligence import DocumentIntelligenceAgent

    state = _build_state(
        req.text, "document_intelligence",
        current_user.get("id"), req.case_id, req.session_id,
    )
    agent = DocumentIntelligenceAgent()
    result = await agent.run(state)

    return {
        "session_id": result["session_id"],
        "document_intelligence": result.get("document_intelligence"),
        "extracted_entities": result.get("extracted_entities"),
        "document_chunks": len(result.get("document_chunks", [])),
        "retrieval_query": result.get("retrieval_query"),
        "errors": result.get("errors", []),
        "warnings": result.get("warnings", []),
    }


@router.post("/document-intelligence/upload")
async def run_document_intelligence_upload(
    file: UploadFile = File(...),
    case_id: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
):
    """Run the Document Intelligence Agent on an uploaded file."""
    import aiofiles
    from app.ai.agents.document_intelligence import DocumentIntelligenceAgent

    # Save upload to temp path
    ext = os.path.splitext(file.filename)[1].lower()
    allowed = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp", ".txt"}
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    tmp_path = os.path.join(settings.UPLOAD_DIR, f"tmp_{uuid.uuid4()}{ext}")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    async with aiofiles.open(tmp_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    try:
        state = _build_state(
            "", "document_intelligence",
            current_user.get("id"), case_id,
            file_paths=[tmp_path],
        )
        agent = DocumentIntelligenceAgent()
        result = await agent.run(state)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return {
        "session_id": result["session_id"],
        "document_intelligence": result.get("document_intelligence"),
        "extracted_entities": result.get("extracted_entities"),
        "document_chunks": len(result.get("document_chunks", [])),
        "errors": result.get("errors", []),
        "warnings": result.get("warnings", []),
    }


# ── 2. Legal Research Agent ───────────────────────────────────────────────────

@router.post("/legal-research/run")
async def run_legal_research(
    req: TextOnlyRequest,
    current_user: dict = Depends(get_current_user),
):
    """Run the Legal Research Agent on raw text (no prior document processing needed)."""
    from app.ai.agents.legal_research import LegalResearchAgent

    state = _build_state(
        req.text, "legal_research",
        current_user.get("id"), req.case_id, req.session_id,
    )
    agent = LegalResearchAgent()
    result = await agent.run(state)

    return {
        "session_id": result["session_id"],
        "legal_research": result.get("legal_research"),
        "errors": result.get("errors", []),
        "warnings": result.get("warnings", []),
    }


# ── 3. Similar Case Retrieval Agent ──────────────────────────────────────────

@router.post("/similar-cases/run")
async def run_similar_cases(
    req: TextOnlyRequest,
    current_user: dict = Depends(get_current_user),
):
    """Run the Similar Case Retrieval Agent on raw text."""
    from app.ai.agents.similar_cases import SimilarCaseRetrievalAgent

    state = _build_state(
        req.text, "similar_cases",
        current_user.get("id"), req.case_id, req.session_id,
    )
    agent = SimilarCaseRetrievalAgent()
    result = await agent.run(state)

    return {
        "session_id": result["session_id"],
        "similar_cases": result.get("similar_cases", []),
        "total_found": len(result.get("similar_cases", [])),
        "errors": result.get("errors", []),
        "warnings": result.get("warnings", []),
    }


# ── 4. Evidence Analysis Agent ────────────────────────────────────────────────

@router.post("/evidence-analysis/run")
async def run_evidence_analysis(
    req: TextOnlyRequest,
    current_user: dict = Depends(get_current_user),
):
    """Run the Evidence Analysis Agent on raw text (simulates evidence description)."""
    from app.ai.agents.evidence_analysis import EvidenceAnalysisAgent

    state = _build_state(
        req.text, "evidence_analysis",
        current_user.get("id"), req.case_id, req.session_id,
    )
    agent = EvidenceAnalysisAgent()
    result = await agent.run(state)

    return {
        "session_id": result["session_id"],
        "evidence_items": result.get("evidence_items", []),
        "evidence_timeline": result.get("evidence_timeline", []),
        "evidence_analysis": result.get("evidence_analysis"),
        "missing_evidence_hints": result.get("missing_evidence_hints", []),
        "errors": result.get("errors", []),
        "warnings": result.get("warnings", []),
    }


@router.post("/evidence-analysis/upload")
async def run_evidence_analysis_upload(
    files: List[UploadFile] = File(...),
    case_text: str = Form(default=""),
    case_id: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
):
    """Run the Evidence Analysis Agent on uploaded evidence files."""
    import aiofiles
    from app.ai.agents.evidence_analysis import EvidenceAnalysisAgent

    allowed_exts = {
        ".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp",
        ".mp3", ".wav", ".mp4", ".avi", ".mov", ".txt", ".eml",
    }
    tmp_paths = []
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    for upload in files:
        ext = os.path.splitext(upload.filename)[1].lower()
        if ext not in allowed_exts:
            continue
        tmp_path = os.path.join(settings.UPLOAD_DIR, f"tmp_{uuid.uuid4()}{ext}")
        async with aiofiles.open(tmp_path, "wb") as f:
            await f.write(await upload.read())
        tmp_paths.append(tmp_path)

    if not tmp_paths:
        raise HTTPException(status_code=400, detail="No supported files provided")

    try:
        state = _build_state(
            case_text, "evidence_analysis",
            current_user.get("id"), case_id,
            file_paths=tmp_paths,
        )
        agent = EvidenceAnalysisAgent()
        result = await agent.run(state)
    finally:
        for p in tmp_paths:
            if os.path.exists(p):
                os.remove(p)

    return {
        "session_id": result["session_id"],
        "evidence_items": result.get("evidence_items", []),
        "evidence_timeline": result.get("evidence_timeline", []),
        "evidence_analysis": result.get("evidence_analysis"),
        "missing_evidence_hints": result.get("missing_evidence_hints", []),
        "errors": result.get("errors", []),
        "warnings": result.get("warnings", []),
    }


# ── 5. Full Phase 3A Pipeline ─────────────────────────────────────────────────

@router.post("/pipeline/phase3a")
async def run_phase3a_pipeline(
    req: Phase3APipelineRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Execute the complete Phase 3A pipeline:
    Document Intelligence → Legal Research → Similar Cases → Evidence Analysis
    """
    from app.ai.orchestrator.graph import LexIntelOrchestrator

    orchestrator = LexIntelOrchestrator()
    result = await orchestrator.run(
        raw_input=req.text,
        pipeline_name="phase3a",
        user_id=current_user.get("id"),
        case_id=req.case_id,
        session_id=req.session_id,
        uploaded_file_paths=req.file_paths,
    )

    return {
        "session_id": result["session_id"],
        "pipeline": "phase3a",
        "document_intelligence": result.get("document_intelligence"),
        "legal_research": result.get("legal_research"),
        "similar_cases": result.get("similar_cases", []),
        "evidence_timeline": result.get("evidence_timeline", []),
        "evidence_analysis": result.get("evidence_analysis"),
        "missing_evidence_hints": result.get("missing_evidence_hints", []),
        "agent_executions": result.get("agent_executions", []),
        "errors": result.get("errors", []),
        "warnings": result.get("warnings", []),
        "metadata": result.get("metadata", {}),
    }


# ── 6. Outcome Prediction Agent ───────────────────────────────────────────────────────────────────────────────────

@router.post("/outcome-prediction/run")
async def run_outcome_prediction(
    req: TextOnlyRequest,
    current_user: dict = Depends(get_current_user),
):
    """Run the Outcome Prediction Agent on raw text (Phase 3B)."""
    from app.ai.agents.outcome_prediction import OutcomePredictionAgent

    state = _build_state(
        req.text, "outcome_prediction",
        current_user.get("id"), req.case_id, req.session_id,
    )
    state["sanitized_input"] = req.text
    result = await OutcomePredictionAgent().run(state)
    return {
        "session_id": result["session_id"],
        "outcome_prediction": result.get("outcome_prediction"),
        "errors": result.get("errors", []),
    }


# ── 7. Strategy Planning Agent ───────────────────────────────────────────────────────────────────────────────────

@router.post("/strategy-planning/run")
async def run_strategy_planning(
    req: TextOnlyRequest,
    current_user: dict = Depends(get_current_user),
):
    """Run the Strategy Planning Agent on raw text (Phase 3B)."""
    from app.ai.agents.strategy_planning import StrategyPlanningAgent

    state = _build_state(
        req.text, "strategy_planning",
        current_user.get("id"), req.case_id, req.session_id,
    )
    state["sanitized_input"] = req.text
    result = await StrategyPlanningAgent().run(state)
    return {
        "session_id": result["session_id"],
        "legal_strategy": result.get("legal_strategy"),
        "errors": result.get("errors", []),
    }


# ── 8. Legal Drafting Agent ────────────────────────────────────────────────────────────────────────────────────────

@router.post("/legal-drafting/run")
async def run_legal_drafting(
    req: TextOnlyRequest,
    current_user: dict = Depends(get_current_user),
):
    """Run the Legal Drafting Agent on raw text (Phase 3B)."""
    from app.ai.agents.legal_drafting import LegalDraftingAgent

    state = _build_state(
        req.text, "legal_drafting",
        current_user.get("id"), req.case_id, req.session_id,
    )
    state["sanitized_input"] = req.text
    result = await LegalDraftingAgent().run(state)
    return {
        "session_id": result["session_id"],
        "legal_drafts": result.get("legal_drafts", []),
        "errors": result.get("errors", []),
    }


# ── 9. Report & Explainability Agent ───────────────────────────────────────────────────────────────────────────────────

@router.post("/report/run")
async def run_report_explainability(
    req: TextOnlyRequest,
    current_user: dict = Depends(get_current_user),
):
    """Run the Report & Explainability Agent on raw text (Phase 3B)."""
    from app.ai.agents.report_explainability import ReportExplainabilityAgent

    state = _build_state(
        req.text, "report",
        current_user.get("id"), req.case_id, req.session_id,
    )
    state["sanitized_input"] = req.text
    result = await ReportExplainabilityAgent().run(state)
    return {
        "session_id": result["session_id"],
        "case_report": result.get("case_report"),
        "errors": result.get("errors", []),
    }


# ── 10. Full Phase 3B Pipeline ───────────────────────────────────────────────────────────────────────────────────

@router.post("/pipeline/phase3b")
async def run_phase3b_pipeline(
    req: Phase3APipelineRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Execute the complete Phase 3B pipeline (all 8 agents):
    Doc Intel → Legal Research → Similar Cases → Evidence →
    Outcome Prediction → Strategy → Drafting → Report
    """
    from app.ai.orchestrator.graph import LexIntelOrchestrator

    orchestrator = LexIntelOrchestrator()
    result = await orchestrator.run(
        raw_input=req.text,
        pipeline_name="phase3b",
        user_id=current_user.get("id"),
        case_id=req.case_id,
        session_id=req.session_id,
        uploaded_file_paths=req.file_paths,
    )

    return {
        "session_id": result["session_id"],
        "pipeline": "phase3b",
        # Phase 3A
        "document_intelligence": result.get("document_intelligence"),
        "legal_research": result.get("legal_research"),
        "similar_cases": result.get("similar_cases", []),
        "evidence_timeline": result.get("evidence_timeline", []),
        "evidence_analysis": result.get("evidence_analysis"),
        "missing_evidence_hints": result.get("missing_evidence_hints", []),
        # Phase 3B
        "outcome_prediction": result.get("outcome_prediction"),
        "legal_strategy": result.get("legal_strategy"),
        "legal_drafts": result.get("legal_drafts", []),
        "case_report": result.get("case_report"),
        # Observability
        "agent_executions": result.get("agent_executions", []),
        "errors": result.get("errors", []),
        "warnings": result.get("warnings", []),
        "metadata": result.get("metadata", {}),
    }


@router.post("/pipeline/phase3a/upload")
async def run_phase3a_pipeline_upload(
    files: List[UploadFile] = File(...),
    case_text: str = Form(default=""),
    case_id: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
):
    """Execute the complete Phase 3A pipeline with file uploads."""
    import aiofiles
    from app.ai.orchestrator.graph import LexIntelOrchestrator

    allowed_exts = {
        ".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp",
        ".mp3", ".wav", ".mp4", ".avi", ".mov", ".txt", ".eml",
    }
    tmp_paths = []
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    for upload in files:
        ext = os.path.splitext(upload.filename)[1].lower()
        if ext not in allowed_exts:
            continue
        tmp_path = os.path.join(settings.UPLOAD_DIR, f"tmp_{uuid.uuid4()}{ext}")
        async with aiofiles.open(tmp_path, "wb") as f:
            await f.write(await upload.read())
        tmp_paths.append(tmp_path)

    if not tmp_paths:
        raise HTTPException(status_code=400, detail="No supported files provided")

    try:
        orchestrator = LexIntelOrchestrator()
        result = await orchestrator.run(
            raw_input=case_text,
            pipeline_name="phase3a",
            user_id=current_user.get("id"),
            case_id=case_id,
            uploaded_file_paths=tmp_paths,
        )
    finally:
        for p in tmp_paths:
            if os.path.exists(p):
                os.remove(p)

    return {
        "session_id": result["session_id"],
        "pipeline": "phase3a",
        "document_intelligence": result.get("document_intelligence"),
        "legal_research": result.get("legal_research"),
        "similar_cases": result.get("similar_cases", []),
        "evidence_timeline": result.get("evidence_timeline", []),
        "evidence_analysis": result.get("evidence_analysis"),
        "missing_evidence_hints": result.get("missing_evidence_hints", []),
        "agent_executions": result.get("agent_executions", []),
        "errors": result.get("errors", []),
        "warnings": result.get("warnings", []),
        "metadata": result.get("metadata", {}),
    }


@router.post("/pipeline/phase3b/upload")
async def run_phase3b_pipeline_upload(
    files: List[UploadFile] = File(...),
    case_text: str = Form(default=""),
    case_id: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
):
    """Execute the complete Phase 3B pipeline (all 8 agents) with file uploads."""
    import aiofiles
    from app.ai.orchestrator.graph import LexIntelOrchestrator

    allowed_exts = {
        ".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp",
        ".mp3", ".wav", ".mp4", ".avi", ".mov", ".txt", ".eml",
    }
    tmp_paths = []
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    for upload in files:
        ext = os.path.splitext(upload.filename)[1].lower()
        if ext not in allowed_exts:
            continue
        tmp_path = os.path.join(settings.UPLOAD_DIR, f"tmp_{uuid.uuid4()}{ext}")
        async with aiofiles.open(tmp_path, "wb") as f:
            await f.write(await upload.read())
        tmp_paths.append(tmp_path)

    if not tmp_paths:
        raise HTTPException(status_code=400, detail="No supported files provided")

    try:
        orchestrator = LexIntelOrchestrator()
        result = await orchestrator.run(
            raw_input=case_text,
            pipeline_name="phase3b",
            user_id=current_user.get("id"),
            case_id=case_id,
            uploaded_file_paths=tmp_paths,
        )
    finally:
        for p in tmp_paths:
            if os.path.exists(p):
                os.remove(p)

    return {
        "session_id": result["session_id"],
        "pipeline": "phase3b",
        "document_intelligence": result.get("document_intelligence"),
        "legal_research": result.get("legal_research"),
        "similar_cases": result.get("similar_cases", []),
        "evidence_timeline": result.get("evidence_timeline", []),
        "evidence_analysis": result.get("evidence_analysis"),
        "missing_evidence_hints": result.get("missing_evidence_hints", []),
        "outcome_prediction": result.get("outcome_prediction"),
        "legal_strategy": result.get("legal_strategy"),
        "legal_drafts": result.get("legal_drafts", []),
        "case_report": result.get("case_report"),
        "agent_executions": result.get("agent_executions", []),
        "errors": result.get("errors", []),
        "warnings": result.get("warnings", []),
        "metadata": result.get("metadata", {}),
    }
