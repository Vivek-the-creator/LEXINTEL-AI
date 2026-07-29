import uuid
from typing import Optional, AsyncIterator
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.core.config import settings
from app.ai.logging.logger import AILogger

router = APIRouter()
logger = AILogger("api.ai")


# ── Request / Response schemas ────────────────────────────────────────────────

class LLMTestRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    system: Optional[str] = None
    stream: bool = False


class AgentRunRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=32000)
    pipeline: str = Field(default="placeholder")
    case_id: Optional[str] = None
    session_id: Optional[str] = None


class MemoryRequest(BaseModel):
    user_id: str
    case_id: Optional[str] = None
    title: Optional[str] = None


class EmbedRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)


class IndexRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000)
    metadata: Optional[dict] = None


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)


# ── Health ────────────────────────────────────────────────────────────────────

@router.get("/health")
async def ai_health():
    """AI infrastructure health check."""
    return {
        "status": "healthy",
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "embedding_model": settings.EMBEDDING_MODEL,
        "groq_configured": bool(settings.GROQ_API_KEY),
    }


# ── LLM ───────────────────────────────────────────────────────────────────────

@router.get("/llm/ping")
async def llm_ping(_: dict = Depends(get_current_user)):
    """Test LLM provider connectivity."""
    from app.ai.llm.service import get_llm_provider
    try:
        provider = get_llm_provider()
        ok = await provider.health_check()
        return {"provider": provider.provider_name, "reachable": ok}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


@router.post("/llm/complete")
async def llm_complete(
    req: LLMTestRequest,
    _: dict = Depends(get_current_user),
):
    """Direct LLM completion — for infrastructure testing only."""
    from app.ai.llm.service import get_llm_provider
    from app.ai.llm.base import LLMConfig
    import re

    # Sanitize
    prompt = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", req.prompt.strip())
    system = req.system or "You are a helpful assistant."

    if req.stream:
        provider = get_llm_provider()

        async def _stream() -> AsyncIterator[bytes]:
            async for chunk in provider.stream(system, prompt):
                yield f"data: {chunk}\n\n".encode()
            yield b"data: [DONE]\n\n"

        return StreamingResponse(_stream(), media_type="text/event-stream")

    provider = get_llm_provider()
    response = await provider.complete(system, prompt)
    return {
        "content": response.content,
        "model": response.model,
        "prompt_tokens": response.prompt_tokens,
        "completion_tokens": response.completion_tokens,
        "total_tokens": response.total_tokens,
        "finish_reason": response.finish_reason,
    }


# ── Agent / Pipeline ──────────────────────────────────────────────────────────

@router.post("/agent/run")
async def run_agent(
    req: AgentRunRequest,
    current_user: dict = Depends(get_current_user),
):
    """Execute a LangGraph pipeline and return the final state."""
    from app.ai.orchestrator.graph import LexIntelOrchestrator

    orchestrator = LexIntelOrchestrator()
    result = await orchestrator.run(
        raw_input=req.text,
        pipeline_name=req.pipeline,
        user_id=current_user.get("id"),
        case_id=req.case_id,
        session_id=req.session_id,
    )
    return {
        "session_id": result["session_id"],
        "pipeline": result["pipeline_name"],
        "response": result.get("current_response"),
        "errors": result.get("errors", []),
        "warnings": result.get("warnings", []),
        "agent_executions": result.get("agent_executions", []),
        "metadata": result.get("metadata", {}),
    }


@router.post("/agent/stream")
async def stream_agent(
    req: AgentRunRequest,
    current_user: dict = Depends(get_current_user),
):
    """Stream LLM output from the placeholder pipeline via SSE."""
    from app.ai.orchestrator.graph import LexIntelOrchestrator

    orchestrator = LexIntelOrchestrator()
    sid = req.session_id or str(uuid.uuid4())

    async def _stream() -> AsyncIterator[bytes]:
        async for chunk in orchestrator.stream(
            raw_input=req.text,
            pipeline_name=req.pipeline,
            user_id=current_user.get("id"),
            session_id=sid,
        ):
            yield f"data: {chunk}\n\n".encode()
        yield b"data: [DONE]\n\n"

    return StreamingResponse(_stream(), media_type="text/event-stream")


# ── Memory ────────────────────────────────────────────────────────────────────

@router.post("/memory/session")
async def create_memory_session(
    req: MemoryRequest,
    _: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Create a new conversation memory session."""
    from app.ai.memory.conversation_memory import ConversationMemory
    memory = ConversationMemory(db)
    session_id = await memory.create_session(
        user_id=req.user_id,
        case_id=req.case_id,
        title=req.title,
    )
    return {"session_id": session_id}


@router.get("/memory/session/{session_id}")
async def get_memory_session(
    session_id: str,
    _: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Retrieve a conversation session with full history."""
    from app.ai.memory.conversation_memory import ConversationMemory
    memory = ConversationMemory(db)
    session = await memory.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/memory/sessions/{user_id}")
async def list_memory_sessions(
    user_id: str,
    case_id: Optional[str] = None,
    _: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """List all conversation sessions for a user."""
    from app.ai.memory.conversation_memory import ConversationMemory
    memory = ConversationMemory(db)
    sessions = await memory.list_sessions(user_id=user_id, case_id=case_id)
    return {"sessions": sessions, "count": len(sessions)}


# ── Embeddings ────────────────────────────────────────────────────────────────

@router.post("/embeddings/embed")
async def embed_text(
    req: EmbedRequest,
    _: dict = Depends(get_current_user),
):
    """Generate an embedding vector for a text string."""
    from app.ai.rag.embedding_service import get_embedding_service
    embedder = get_embedding_service()
    vector = embedder.embed_text(req.text)
    return {
        "model": embedder.model_name,
        "dimension": embedder.dimension,
        "vector_preview": vector[:8],  # first 8 dims for inspection
        "vector_length": len(vector),
    }


# ── Vector Store ──────────────────────────────────────────────────────────────

@router.post("/vector/index")
async def index_document(
    req: IndexRequest,
    _: dict = Depends(get_current_user),
):
    """Chunk, embed, and index a text document into FAISS."""
    from app.ai.rag.pipeline import get_rag_pipeline
    pipeline = get_rag_pipeline()
    chunk_ids = pipeline.index_text(req.text, metadata=req.metadata or {})
    return {
        "indexed_chunks": len(chunk_ids),
        "chunk_ids": chunk_ids,
        "total_indexed": pipeline.total_indexed,
    }


@router.post("/vector/search")
async def vector_search(
    req: SearchRequest,
    _: dict = Depends(get_current_user),
):
    """Semantic similarity search over the FAISS index."""
    from app.ai.rag.pipeline import get_rag_pipeline
    pipeline = get_rag_pipeline()
    results = pipeline.retrieve(req.query, top_k=req.top_k, threshold=req.threshold)
    return {
        "query": req.query,
        "results": results,
        "count": len(results),
        "total_indexed": pipeline.total_indexed,
    }


@router.get("/vector/stats")
async def vector_stats(_: dict = Depends(get_current_user)):
    """Return FAISS index statistics."""
    from app.ai.rag.faiss_store import get_vector_store
    store = get_vector_store()
    return {
        "total_vectors": store.total_vectors,
        "dimension": store.dimension,
        "index_name": settings.VECTOR_STORE_INDEX_NAME,
        "store_dir": settings.VECTOR_STORE_DIR,
    }


# ── Prompts ───────────────────────────────────────────────────────────────────

@router.get("/prompts")
async def list_prompts(_: dict = Depends(get_current_user)):
    """List all registered prompts in the prompt registry."""
    from app.ai.prompts.registry import prompt_registry
    return {"prompts": prompt_registry.list_prompts()}
