from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class CaseStatus(str, Enum):
    DRAFT = "draft"
    ANALYZED = "analyzed"
    ARCHIVED = "archived"


class CaseFileMetaSchema(BaseModel):
    file_id: str
    original_name: str
    relative_path: str
    extension: str
    size_bytes: int
    classification: str
    mime_type: Optional[str] = None


class SaveCaseRequest(BaseModel):
    case_name: str = Field(..., min_length=1, max_length=200)
    session_id: str
    # Phase 3A outputs
    document_intelligence: Optional[Dict[str, Any]] = None
    legal_research: Optional[Dict[str, Any]] = None
    similar_cases: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_items: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_timeline: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_analysis: Optional[Dict[str, Any]] = None
    missing_evidence_hints: List[str] = Field(default_factory=list)
    # Phase 3B outputs
    outcome_prediction: Optional[Dict[str, Any]] = None
    legal_strategy: Optional[Dict[str, Any]] = None
    legal_drafts: List[Dict[str, Any]] = Field(default_factory=list)
    case_report: Optional[Dict[str, Any]] = None
    # Observability
    agent_executions: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    # Case workspace metadata (no file blobs)
    case_workspace: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AddFilesRequest(BaseModel):
    """Request to attach additional file IDs (already uploaded) to a case."""
    file_ids: List[str] = Field(..., min_items=1)


class CaseResponse(BaseModel):
    id: str
    case_name: str
    status: CaseStatus
    created_by: str
    created_at: datetime
    updated_at: datetime
    session_id: str
    document_count: int
    evidence_count: int
    summary: Optional[str] = None
    # Phase 3A
    document_intelligence: Optional[Dict[str, Any]] = None
    legal_research: Optional[Dict[str, Any]] = None
    similar_cases: List[Dict[str, Any]] = []
    evidence_items: List[Dict[str, Any]] = []
    evidence_timeline: List[Dict[str, Any]] = []
    evidence_analysis: Optional[Dict[str, Any]] = None
    missing_evidence_hints: List[str] = []
    # Phase 3B
    outcome_prediction: Optional[Dict[str, Any]] = None
    legal_strategy: Optional[Dict[str, Any]] = None
    legal_drafts: List[Dict[str, Any]] = []
    case_report: Optional[Dict[str, Any]] = None
    # Observability
    agent_executions: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []
    warnings: List[str] = []
    case_workspace: Optional[Dict[str, Any]] = None
    attached_file_ids: List[str] = []
    metadata: Dict[str, Any] = {}

    class Config:
        from_attributes = True


class CaseListResponse(BaseModel):
    items: List[CaseResponse]
    total: int
    page: int
    page_size: int
