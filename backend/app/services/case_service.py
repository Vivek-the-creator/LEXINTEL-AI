from datetime import datetime, timezone
from typing import Optional, List
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.case import SaveCaseRequest, CaseStatus


def _serialize(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


async def save_case(
    db: AsyncIOMotorDatabase,
    req: SaveCaseRequest,
    user_id: str,
) -> dict:
    doc_intel = req.document_intelligence or {}
    summary = doc_intel.get("summary", "")
    doc_count = len((req.case_workspace or {}).get("files", [])) if req.case_workspace else 0

    now = datetime.now(timezone.utc)
    doc = {
        "case_name": req.case_name,
        "status": CaseStatus.ANALYZED.value,
        "created_by": user_id,
        "created_at": now,
        "updated_at": now,
        "session_id": req.session_id,
        "document_count": doc_count,
        "evidence_count": len(req.evidence_items),
        "summary": summary,
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
        "attached_file_ids": [],
        "metadata": req.metadata,
    }
    result = await db.cases.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize(doc)


async def get_case(
    db: AsyncIOMotorDatabase,
    case_id: str,
    user_id: str,
) -> Optional[dict]:
    try:
        doc = await db.cases.find_one({"_id": ObjectId(case_id), "created_by": user_id})
    except Exception:
        return None
    return _serialize(doc) if doc else None


async def list_cases(
    db: AsyncIOMotorDatabase,
    user_id: str,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    skip = (page - 1) * page_size
    cursor = (
        db.cases.find({"created_by": user_id})
        .sort("created_at", -1)
        .skip(skip)
        .limit(page_size)
    )
    items = [_serialize(doc) async for doc in cursor]
    total = await db.cases.count_documents({"created_by": user_id})
    return {"items": items, "total": total, "page": page, "page_size": page_size}


async def delete_case(
    db: AsyncIOMotorDatabase,
    case_id: str,
    user_id: str,
) -> bool:
    try:
        result = await db.cases.delete_one({"_id": ObjectId(case_id), "created_by": user_id})
    except Exception:
        return False
    return result.deleted_count > 0


async def attach_files_to_case(
    db: AsyncIOMotorDatabase,
    case_id: str,
    user_id: str,
    file_ids: List[str],
) -> Optional[dict]:
    try:
        result = await db.cases.find_one_and_update(
            {"_id": ObjectId(case_id), "created_by": user_id},
            {
                "$addToSet": {"attached_file_ids": {"$each": file_ids}},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
            return_document=True,
        )
    except Exception:
        return None
    return _serialize(result) if result else None


async def update_case_analysis(
    db: AsyncIOMotorDatabase,
    case_id: str,
    user_id: str,
    analysis: dict,
) -> Optional[dict]:
    """Merge new AI analysis results into an existing case (for re-analysis)."""
    try:
        result = await db.cases.find_one_and_update(
            {"_id": ObjectId(case_id), "created_by": user_id},
            {"$set": {**analysis, "updated_at": datetime.now(timezone.utc)}},
            return_document=True,
        )
    except Exception:
        return None
    return _serialize(result) if result else None
