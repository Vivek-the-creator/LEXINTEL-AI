"""
Case Workspace API routes.

POST   /api/cases/analyze          — Run full pipeline on uploaded files (SSE stream)
POST   /api/cases/                 — Save AI results as a named case
GET    /api/cases/                 — List user's saved cases
GET    /api/cases/{id}             — Get a single case
DELETE /api/cases/{id}             — Delete a case
POST   /api/cases/{id}/files       — Attach additional uploaded files
POST   /api/cases/{id}/reanalyze   — Re-run pipeline on newly attached files (SSE stream)
"""
import uuid
import os
import json
import asyncio
import tempfile
from typing import Optional, List, AsyncIterator

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.core.config import settings
from app.ai.logging.logger import AILogger
from app.ai.orchestrator.state import create_initial_state
from app.ai.agents.file_classifier import build_case_workspace, SUPPORTED_EXTENSIONS
from app.schemas.case import SaveCaseRequest, AddFilesRequest, CaseResponse, CaseListResponse
from app.services.case_service import (
    save_case, get_case, list_cases, delete_case,
    attach_files_to_case, update_case_analysis,
)

router = APIRouter()
logger = AILogger("api.cases")

# ── SSE helpers ───────────────────────────────────────────────────────────────

def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def _run_pipeline_with_progress(
    file_tuples: List[tuple],   # [(rel_path, abs_path), ...]
    case_name: str,
    user_id: str,
    case_id: Optional[str] = None,
    session_id: Optional[str] = None,
    pipeline_name: str = "phase3b",
) -> AsyncIterator[str]:
    """
    Runs the pipeline while yielding SSE progress events.
    pipeline_name="phase3b" runs all 8 agents (3A + 3B).
    pipeline_name="phase3a" runs only the 4 Phase 3A agents.
    """
    from app.ai.agents.document_intelligence import DocumentIntelligenceAgent
    from app.ai.agents.legal_research import LegalResearchAgent
    from app.ai.agents.similar_cases import SimilarCaseRetrievalAgent
    from app.ai.agents.evidence_analysis import EvidenceAnalysisAgent
    from app.ai.agents.outcome_prediction import OutcomePredictionAgent
    from app.ai.agents.strategy_planning import StrategyPlanningAgent
    from app.ai.agents.legal_drafting import LegalDraftingAgent
    from app.ai.agents.report_explainability import ReportExplainabilityAgent

    sid = session_id or str(uuid.uuid4())
    total_files = len(file_tuples)

    yield _sse("progress", {
        "stage": "Scanning Case",
        "agent": "File Classifier",
        "current_file": None,
        "files_done": 0,
        "files_total": total_files,
        "message": f"Classifying {total_files} files…",
    })
    await asyncio.sleep(0)

    workspace = build_case_workspace(case_name, file_tuples)
    abs_paths = [f["absolute_path"] for f in workspace["files"]]

    yield _sse("progress", {
        "stage": "Scanning Case",
        "agent": "File Classifier",
        "current_file": None,
        "files_done": 0,
        "files_total": total_files,
        "message": f"Found {total_files} supported files. Starting analysis…",
        "classifications": {k: len(v) for k, v in workspace["classifications"].items()},
    })
    await asyncio.sleep(0)

    state = create_initial_state(
        session_id=sid,
        pipeline_name=pipeline_name,
        user_id=user_id,
        case_id=case_id,
        case_name=case_name,
        uploaded_file_paths=abs_paths,
        case_workspace=workspace,
    )

    phase3a_agents = [
        ("Document Intelligence", "Extracting text, entities, and document structure…", DocumentIntelligenceAgent),
        ("Legal Research",        "Researching applicable laws and provisions…",        LegalResearchAgent),
        ("Similar Cases",         "Searching for similar judgments…",                   SimilarCaseRetrievalAgent),
        ("Evidence Analysis",     "Building evidence timeline and inventory…",          EvidenceAnalysisAgent),
    ]
    phase3b_agents = [
        ("Outcome Prediction",    "Predicting case outcome probabilities…",             OutcomePredictionAgent),
        ("Strategy Planning",     "Generating legal strategies…",                       StrategyPlanningAgent),
        ("Legal Drafting",        "Drafting legal documents…",                          LegalDraftingAgent),
        ("Report & Explainability", "Generating comprehensive case report…",           ReportExplainabilityAgent),
    ]

    agents = phase3a_agents + (phase3b_agents if pipeline_name == "phase3b" else [])
    files_done = 0

    for i, (agent_label, agent_msg, AgentClass) in enumerate(agents):
        if i == 0:
            for j, cf in enumerate(workspace["files"]):
                yield _sse("progress", {
                    "stage": "Document Intelligence",
                    "agent": "Document Intelligence Agent",
                    "current_file": cf["relative_path"],
                    "files_done": j,
                    "files_total": total_files,
                    "message": f"Processing {cf['original_name']}…",
                })
                await asyncio.sleep(0)

        yield _sse("agent_start", {
            "agent": agent_label,
            "message": agent_msg,
            "files_done": files_done,
            "files_total": total_files,
        })
        await asyncio.sleep(0)

        try:
            agent = AgentClass()
            state = await agent.run(state)
            files_done = min(total_files, int(total_files * (i + 1) / len(agents)))
            yield _sse("agent_done", {
                "agent": agent_label,
                "files_done": files_done,
                "files_total": total_files,
                "elapsed_ms": next(
                    (e.get("elapsed_ms") for e in reversed(state.get("agent_executions", []))
                     if e.get("agent") == agent_label.lower().replace(" ", "_")),
                    None,
                ),
            })
        except Exception as exc:
            yield _sse("error", {"agent": agent_label, "error": str(exc)})

        await asyncio.sleep(0)

    yield _sse("complete", {
        "session_id": sid,
        "case_name": case_name,
        # Phase 3A
        "document_intelligence": state.get("document_intelligence"),
        "legal_research": state.get("legal_research"),
        "similar_cases": state.get("similar_cases", []),
        "evidence_items": state.get("evidence_items", []),
        "evidence_timeline": state.get("evidence_timeline", []),
        "evidence_analysis": state.get("evidence_analysis"),
        "missing_evidence_hints": state.get("missing_evidence_hints", []),
        # Phase 3B
        "outcome_prediction": state.get("outcome_prediction"),
        "legal_strategy": state.get("legal_strategy"),
        "legal_drafts": state.get("legal_drafts", []),
        "case_report": state.get("case_report"),
        # Observability
        "agent_executions": state.get("agent_executions", []),
        "errors": state.get("errors", []),
        "warnings": state.get("warnings", []),
        "case_workspace": workspace,
        "metadata": state.get("metadata", {}),
    })


# ── 1. Analyze — stream SSE (multipart upload) ────────────────────────────────

@router.post("/analyze")
async def analyze_case_workspace(
    files: List[UploadFile] = File(...),
    case_name: str = Form(default="Untitled Case"),
    relative_paths: str = Form(default="[]"),   # JSON array of relative paths
    current_user: dict = Depends(get_current_user),
):
    """
    Accept a batch of files with their relative paths (preserving folder structure).
    Stream SSE progress events while running the full Phase 3A pipeline.
    """
    try:
        rel_paths: List[str] = json.loads(relative_paths)
    except Exception:
        rel_paths = []

    # Pad / trim rel_paths to match files count
    while len(rel_paths) < len(files):
        rel_paths.append(files[len(rel_paths)].filename or f"file_{len(rel_paths)}")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    tmp_paths: List[str] = []
    file_tuples: List[tuple] = []

    for upload, rel_path in zip(files, rel_paths):
        ext = os.path.splitext(upload.filename or "")[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            continue
        tmp_path = os.path.join(settings.UPLOAD_DIR, f"tmp_{uuid.uuid4()}{ext}")
        async with aiofiles.open(tmp_path, "wb") as f:
            await f.write(await upload.read())
        tmp_paths.append(tmp_path)
        file_tuples.append((rel_path, tmp_path))

    if not file_tuples:
        raise HTTPException(status_code=400, detail="No supported files provided")

    user_id = current_user.get("id")

    async def event_stream():
        try:
            async for chunk in _run_pipeline_with_progress(
                file_tuples, case_name, user_id, pipeline_name="phase3b"
            ):
                yield chunk
        finally:
            for p in tmp_paths:
                try:
                    if os.path.exists(p):
                        os.remove(p)
                except Exception:
                    pass

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── 2. Analyze from existing uploaded file IDs ────────────────────────────────

@router.post("/analyze-saved")
async def analyze_saved_files(
    file_ids: List[str] = Form(...),
    case_name: str = Form(default="Untitled Case"),
    current_user: dict = Depends(get_current_user),
):
    """Run pipeline on files already stored in the uploads directory."""
    file_tuples: List[tuple] = []
    for fid in file_ids:
        # fid may be a stored filename like "abc123.pdf"
        path = os.path.join(settings.UPLOAD_DIR, fid)
        if os.path.exists(path):
            file_tuples.append((os.path.basename(path), path))

    if not file_tuples:
        raise HTTPException(status_code=400, detail="No valid file IDs provided")

    user_id = current_user.get("id")

    async def event_stream():
        async for chunk in _run_pipeline_with_progress(
            file_tuples, case_name, user_id, pipeline_name="phase3b"
        ):
            yield chunk

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── 3. Save case ──────────────────────────────────────────────────────────────

@router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    req: SaveCaseRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await save_case(db, req, current_user["id"])
    return doc


# ── 4. List cases ─────────────────────────────────────────────────────────────

@router.get("/", response_model=CaseListResponse)
async def list_user_cases(
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20
    return await list_cases(db, current_user["id"], page, page_size)


# ── 5. Get single case ────────────────────────────────────────────────────────

@router.get("/{case_id}", response_model=CaseResponse)
async def get_single_case(
    case_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    case = await get_case(db, case_id, current_user["id"])
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


# ── 6. Delete case ────────────────────────────────────────────────────────────

@router.delete("/{case_id}")
async def remove_case(
    case_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    deleted = await delete_case(db, case_id, current_user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Case not found")
    return {"success": True, "message": "Case deleted"}


# ── 7. Attach additional files ────────────────────────────────────────────────

@router.post("/{case_id}/files")
async def attach_files(
    case_id: str,
    req: AddFilesRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    case = await attach_files_to_case(db, case_id, current_user["id"], req.file_ids)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return {"success": True, "attached_file_ids": case.get("attached_file_ids", [])}


# ── 8. Re-analyze case (newly attached files only) ────────────────────────────

@router.post("/{case_id}/reanalyze")
async def reanalyze_case(
    case_id: str,
    files: List[UploadFile] = File(...),
    relative_paths: str = Form(default="[]"),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """
    Upload new evidence files for an existing case and re-run the pipeline.
    Streams SSE progress. On completion, caller should PATCH the case via /api/cases/{id}.
    """
    case = await get_case(db, case_id, current_user["id"])
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        rel_paths: List[str] = json.loads(relative_paths)
    except Exception:
        rel_paths = []

    while len(rel_paths) < len(files):
        rel_paths.append(files[len(rel_paths)].filename or f"file_{len(rel_paths)}")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    tmp_paths: List[str] = []
    file_tuples: List[tuple] = []

    for upload, rel_path in zip(files, rel_paths):
        ext = os.path.splitext(upload.filename or "")[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            continue
        tmp_path = os.path.join(settings.UPLOAD_DIR, f"tmp_{uuid.uuid4()}{ext}")
        async with aiofiles.open(tmp_path, "wb") as f:
            await f.write(await upload.read())
        tmp_paths.append(tmp_path)
        file_tuples.append((rel_path, tmp_path))

    if not file_tuples:
        raise HTTPException(status_code=400, detail="No supported files provided")

    user_id = current_user.get("id")
    case_name = case.get("case_name", "Case")

    async def event_stream():
        try:
            async for chunk in _run_pipeline_with_progress(
                file_tuples, case_name, user_id, case_id=case_id, pipeline_name="phase3b"
            ):
                yield chunk
        finally:
            for p in tmp_paths:
                try:
                    if os.path.exists(p):
                        os.remove(p)
                except Exception:
                    pass

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── 9. Update case with new analysis results ──────────────────────────────────

@router.patch("/{case_id}/analysis")
async def patch_case_analysis(
    case_id: str,
    req: SaveCaseRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Merge new AI analysis results into an existing case after re-analysis."""
    analysis = {
        # Phase 3A
        "document_intelligence": req.document_intelligence,
        "legal_research": req.legal_research,
        "similar_cases": req.similar_cases,
        "evidence_items": req.evidence_items,
        "evidence_timeline": req.evidence_timeline,
        "evidence_analysis": req.evidence_analysis,
        "missing_evidence_hints": req.missing_evidence_hints,
        # Phase 3B
        "outcome_prediction": req.outcome_prediction,
        "legal_strategy": req.legal_strategy,
        "legal_drafts": req.legal_drafts,
        "case_report": req.case_report,
        # Observability
        "agent_executions": req.agent_executions,
        "errors": req.errors,
        "warnings": req.warnings,
        "case_workspace": req.case_workspace,
        "evidence_count": len(req.evidence_items),
        "summary": (req.document_intelligence or {}).get("summary", ""),
    }
    case = await update_case_analysis(db, case_id, current_user["id"], analysis)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case
