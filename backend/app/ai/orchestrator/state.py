from typing import TypedDict, Optional, List, Dict, Any, Literal
from datetime import datetime


class DocumentChunk(TypedDict):
    chunk_id: str
    text: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]]


class ConversationMessage(TypedDict):
    role: str          # "user" | "assistant" | "system"
    content: str
    timestamp: str
    agent: Optional[str]


class AgentError(TypedDict):
    agent: str
    error: str
    timestamp: str
    recoverable: bool


class AgentExecutionMeta(TypedDict):
    agent: str
    started_at: str
    finished_at: Optional[str]
    elapsed_ms: Optional[float]
    status: str        # "pending" | "running" | "done" | "failed" | "skipped"


# ── Phase 3B — Case Workspace types ─────────────────────────────────────────

FileClassificationLabel = Literal[
    "legal_document", "image", "video", "audio",
    "chat", "email", "spreadsheet", "text", "unknown"
]


class CaseFile(TypedDict):
    """A single file inside a Case Workspace."""
    file_id: str                    # uuid
    original_name: str              # original filename
    relative_path: str              # path relative to case root folder
    absolute_path: str              # absolute path on disk (temp or stored)
    extension: str
    size_bytes: int
    classification: FileClassificationLabel
    mime_type: Optional[str]
    hash: Optional[str]             # SHA-256 for dedup


class CaseWorkspace(TypedDict):
    """Represents the full set of files in a case."""
    case_name: str
    total_files: int
    files: List[CaseFile]
    folder_structure: Dict[str, Any]   # nested dict mirroring folder tree
    classifications: Dict[str, List[str]]  # label → [file_ids]


# ── Phase 3A typed sub-structures ─────────────────────────────────────────────

class ExtractedEntity(TypedDict):
    text: str
    label: str          # PERSON | ORG | DATE | LOCATION | LEGAL_SECTION | CASE_REF
    confidence: float
    context: Optional[str]


class DocumentIntelligenceResult(TypedDict):
    document_type: str          # FIR | JUDGMENT | CONTRACT | PETITION | AFFIDAVIT | UNKNOWN
    summary: str
    language: str
    page_count: int
    ocr_used: bool
    confidence: float
    parties: List[str]
    organizations: List[str]
    locations: List[str]
    dates: List[str]
    legal_sections: List[str]
    entities: List[ExtractedEntity]
    raw_text: str


class LegalProvision(TypedDict):
    act: str
    section: str
    title: str
    description: str
    relevance_score: float
    plain_language: str


class LegalResearchResult(TypedDict):
    applicable_acts: List[str]
    provisions: List[LegalProvision]
    remedies: List[str]
    legal_principles: List[str]
    rag_chunks_used: int
    research_summary: str


class SimilarCase(TypedDict):
    case_name: str
    citation: str
    court: str
    year: Optional[str]
    similarity_score: float
    summary: str
    verdict: str
    key_principles: List[str]


class EvidenceItem(TypedDict):
    evidence_id: str
    file_name: str
    file_type: str          # pdf | image | audio | video | text | email | whatsapp
    file_size_bytes: int
    timestamp: Optional[str]
    extracted_timestamp: Optional[str]
    category: str           # documentary | digital | physical | testimonial
    description: str
    metadata: Dict[str, Any]
    is_duplicate: bool
    duplicate_of: Optional[str]
    hash: Optional[str]


class EvidenceTimelineEntry(TypedDict):
    timestamp: str
    event_description: str
    evidence_ids: List[str]
    confidence: float


# ── Main shared state ─────────────────────────────────────────────────────────

class LexIntelState(TypedDict):
    """
    Shared state object that flows through every LangGraph node.
    Each Phase 3A agent enriches this progressively.
    """

    # ── Session / Identity ────────────────────────────────────────────────────
    session_id: str
    user_id: Optional[str]
    case_id: Optional[str]
    pipeline_name: str

    # ── Input ─────────────────────────────────────────────────────────────────
    raw_input: Optional[str]
    sanitized_input: Optional[str]

    # ── Case Workspace ───────────────────────────────────────────────────────
    case_name: Optional[str]
    case_workspace: Optional[CaseWorkspace]

    # ── Document Processing ───────────────────────────────────────────────────
    uploaded_file_ids: List[str]
    uploaded_file_paths: List[str]          # absolute paths on disk
    document_chunks: List[DocumentChunk]
    extracted_entities: Dict[str, Any]      # legacy flat dict (kept for compat)
    document_intelligence: Optional[DocumentIntelligenceResult]

    # ── RAG / Retrieval ───────────────────────────────────────────────────────
    retrieval_query: Optional[str]
    retrieved_chunks: List[DocumentChunk]
    rag_context: Optional[str]

    # ── Legal Research ────────────────────────────────────────────────────────
    research_results: List[Dict[str, Any]]  # legacy (kept for compat)
    legal_research: Optional[LegalResearchResult]

    # ── Similar Cases ─────────────────────────────────────────────────────────
    similar_cases: List[SimilarCase]

    # ── Evidence ──────────────────────────────────────────────────────────────
    evidence_items: List[EvidenceItem]
    evidence_timeline: List[EvidenceTimelineEntry]
    evidence_analysis: Optional[Dict[str, Any]]
    missing_evidence_hints: List[str]

    # ── Phase 3B — Prediction & Strategy ────────────────────────────────────
    outcome_prediction: Optional[Dict[str, Any]]
    legal_strategy: Optional[Dict[str, Any]]
    legal_drafts: List[Dict[str, Any]]
    case_report: Optional[Dict[str, Any]]

    # ── Legacy (kept for compat) ──────────────────────────────────────────────
    draft_document: Optional[str]
    final_report: Optional[str]

    # ── Conversation Memory ───────────────────────────────────────────────────
    conversation_history: List[ConversationMessage]
    current_response: Optional[str]

    # ── Orchestration Metadata ────────────────────────────────────────────────
    agent_executions: List[AgentExecutionMeta]
    errors: List[AgentError]
    warnings: List[str]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str


def create_initial_state(
    session_id: str,
    pipeline_name: str,
    raw_input: Optional[str] = None,
    user_id: Optional[str] = None,
    case_id: Optional[str] = None,
    case_name: Optional[str] = None,
    uploaded_file_paths: Optional[List[str]] = None,
    uploaded_file_ids: Optional[List[str]] = None,
    case_workspace: Optional[CaseWorkspace] = None,
) -> LexIntelState:
    """Factory for a clean initial state."""
    now = datetime.utcnow().isoformat()
    return LexIntelState(
        session_id=session_id,
        user_id=user_id,
        case_id=case_id,
        case_name=case_name,
        case_workspace=case_workspace,
        pipeline_name=pipeline_name,
        raw_input=raw_input,
        sanitized_input=None,
        uploaded_file_ids=uploaded_file_ids or [],
        uploaded_file_paths=uploaded_file_paths or [],
        document_chunks=[],
        extracted_entities={},
        document_intelligence=None,
        retrieval_query=None,
        retrieved_chunks=[],
        rag_context=None,
        research_results=[],
        legal_research=None,
        similar_cases=[],
        evidence_items=[],
        evidence_timeline=[],
        evidence_analysis=None,
        missing_evidence_hints=[],
        outcome_prediction=None,
        legal_strategy=None,
        legal_drafts=[],
        case_report=None,
        draft_document=None,
        final_report=None,
        conversation_history=[],
        current_response=None,
        agent_executions=[],
        errors=[],
        warnings=[],
        metadata={},
        created_at=now,
        updated_at=now,
    )
