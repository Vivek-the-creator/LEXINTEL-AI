"""
Chat API — streaming legal assistant chatbot with conversation memory.

POST /api/chat/message          — send a message, get SSE streamed reply
POST /api/chat/session          — create a new session
GET  /api/chat/sessions         — list user sessions
GET  /api/chat/session/{id}     — get session with history
DELETE /api/chat/session/{id}   — delete session
"""
import uuid
from typing import Optional, AsyncIterator
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.ai.memory.conversation_memory import ConversationMemory
from app.ai.logging.logger import AILogger

router = APIRouter()
logger = AILogger("api.chat")


class NewSessionRequest(BaseModel):
    title: Optional[str] = "New Conversation"
    case_id: Optional[str] = None


class ChatMessageRequest(BaseModel):
    session_id: str
    message: str = Field(..., min_length=1, max_length=8000)
    case_id: Optional[str] = None


@router.post("/session")
async def create_session(
    req: NewSessionRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    memory = ConversationMemory(db)
    session_id = await memory.create_session(
        user_id=current_user["id"],
        case_id=req.case_id,
        title=req.title or "New Conversation",
    )
    return {"session_id": session_id, "title": req.title}


@router.get("/sessions")
async def list_sessions(
    case_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    memory = ConversationMemory(db)
    sessions = await memory.list_sessions(user_id=current_user["id"], case_id=case_id)
    return {"sessions": sessions}


@router.get("/session/{session_id}")
async def get_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    memory = ConversationMemory(db)
    session = await memory.get_session(session_id)
    if not session or session.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    memory = ConversationMemory(db)
    deleted = await memory.delete_session(session_id, current_user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"success": True}


@router.post("/message")
async def send_message(
    req: ChatMessageRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """
    Stream a legal assistant reply via SSE.
    Loads conversation history + optional case context, then streams LLM response.
    """
    memory = ConversationMemory(db)

    # Verify session belongs to user
    session = await memory.get_session(req.session_id)
    if not session or session.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=404, detail="Session not found")

    # Save user message
    await memory.add_message(req.session_id, "user", req.message)

    # Build history string (last 10 turns)
    history_msgs = await memory.get_history(req.session_id, limit=10)
    # Exclude the message we just added (last one) for the history context
    prior = history_msgs[:-1] if history_msgs else []
    history_str = "\n".join(
        f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
        for m in prior[-8:]
    ) or "None"

    # Build case context if case_id provided
    case_context = ""
    case_id = req.case_id or session.get("case_id")
    if case_id:
        try:
            case_doc = await db["cases"].find_one({"_id": __import__("bson").ObjectId(case_id)})
            if case_doc:
                di = case_doc.get("document_intelligence") or {}
                lr = case_doc.get("legal_research") or {}
                op = case_doc.get("outcome_prediction") or {}
                ea = case_doc.get("evidence_analysis") or {}
                case_context = (
                    f"CASE CONTEXT — {case_doc.get('case_name', 'Untitled Case')}:\n"
                    f"Summary: {di.get('summary', '')}\n"
                    f"Document Type: {di.get('document_type', '')}\n"
                    f"Parties: {', '.join(di.get('parties') or [])}\n"
                    f"Applicable Laws: {', '.join(lr.get('applicable_acts') or [])}\n"
                    f"Legal Sections: {', '.join(di.get('legal_sections') or [])}\n"
                    f"Outcome Prediction: {op.get('probability_of_success', 'N/A')} success probability\n"
                    f"Evidence Summary: {ea.get('analysis_summary', '')}\n"
                    f"Remedies: {'; '.join((lr.get('remedies') or [])[:4])}\n\n"
                )
        except Exception:
            pass

    from app.ai.prompts.registry import prompt_registry
    from app.ai.llm.service import get_llm_provider

    prompt = prompt_registry.get("legal_chat")
    user_prompt = prompt.render_user(
        case_context=case_context,
        history=history_str,
        question=req.message[:4000],
    )

    llm = get_llm_provider()
    full_reply = []

    async def _stream() -> AsyncIterator[bytes]:
        try:
            async for chunk in llm.stream(prompt.system, user_prompt):
                full_reply.append(chunk)
                yield f"data: {chunk}\n\n".encode()
            yield b"data: [DONE]\n\n"
        finally:
            # Persist assistant reply after streaming completes
            reply_text = "".join(full_reply)
            if reply_text:
                import asyncio
                asyncio.create_task(
                    memory.add_message(req.session_id, "assistant", reply_text, agent="legal_chat")
                )

    return StreamingResponse(
        _stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
