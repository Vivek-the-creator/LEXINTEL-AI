import uuid
from datetime import datetime, timezone
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.ai.orchestrator.state import ConversationMessage
from app.ai.logging.logger import AILogger
from app.core.config import settings

logger = AILogger("memory")


class ConversationMemory:
    """
    Persistent multi-turn conversation memory stored in MongoDB.
    Every AI agent can read/write through this service.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self._col = db[settings.MEMORY_COLLECTION]

    async def create_session(
        self,
        user_id: str,
        case_id: Optional[str] = None,
        title: Optional[str] = None,
    ) -> str:
        session_id = str(uuid.uuid4())
        doc = {
            "session_id": session_id,
            "user_id": user_id,
            "case_id": case_id,
            "title": title or "New Conversation",
            "messages": [],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        await self._col.insert_one(doc)
        logger.info("Session created", session_id=session_id, user_id=user_id)
        return session_id

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        agent: Optional[str] = None,
    ) -> None:
        message: ConversationMessage = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": agent,
        }
        await self._col.update_one(
            {"session_id": session_id},
            {
                "$push": {
                    "messages": {
                        "$each": [message],
                        "$slice": -settings.MEMORY_MAX_HISTORY,
                    }
                },
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
        )

    async def get_history(
        self, session_id: str, limit: Optional[int] = None
    ) -> List[ConversationMessage]:
        doc = await self._col.find_one({"session_id": session_id}, {"messages": 1})
        if not doc:
            return []
        messages = doc.get("messages", [])
        if limit:
            messages = messages[-limit:]
        return messages

    async def get_session(self, session_id: str) -> Optional[dict]:
        doc = await self._col.find_one(
            {"session_id": session_id}, {"_id": 0}
        )
        return doc

    async def list_sessions(
        self, user_id: str, case_id: Optional[str] = None, limit: int = 20
    ) -> List[dict]:
        query: dict = {"user_id": user_id}
        if case_id:
            query["case_id"] = case_id
        cursor = (
            self._col.find(query, {"_id": 0, "messages": 0})
            .sort("updated_at", -1)
            .limit(limit)
        )
        return [doc async for doc in cursor]

    async def delete_session(self, session_id: str, user_id: str) -> bool:
        result = await self._col.delete_one(
            {"session_id": session_id, "user_id": user_id}
        )
        return result.deleted_count > 0

    async def clear_history(self, session_id: str) -> None:
        await self._col.update_one(
            {"session_id": session_id},
            {"$set": {"messages": [], "updated_at": datetime.now(timezone.utc)}},
        )
