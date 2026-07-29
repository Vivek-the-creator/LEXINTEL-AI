from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.security import hash_password, verify_password
from app.schemas.user import UserRegisterRequest, UserRole


def _serialize_user(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    doc.pop("password", None)
    return doc


async def create_user(db: AsyncIOMotorDatabase, data: UserRegisterRequest) -> dict:
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise ValueError("An account with this email already exists")

    user_doc = {
        "full_name": data.full_name,
        "email": data.email,
        "password": hash_password(data.password),
        "role": data.role.value,
        "avatar_url": None,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    return _serialize_user(user_doc)


async def authenticate_user(db: AsyncIOMotorDatabase, email: str, password: str) -> dict:
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(password, user["password"]):
        raise ValueError("Invalid email or password")
    if not user.get("is_active", True):
        raise ValueError("Account is deactivated")
    return _serialize_user(user)


async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: str) -> Optional[dict]:
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None
    if not user:
        return None
    return _serialize_user(user)


async def update_user(db: AsyncIOMotorDatabase, user_id: str, updates: dict) -> Optional[dict]:
    updates["updated_at"] = datetime.now(timezone.utc)
    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": updates})
    return await get_user_by_id(db, user_id)


async def change_user_password(
    db: AsyncIOMotorDatabase, user_id: str, current_password: str, new_password: str
) -> bool:
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user or not verify_password(current_password, user["password"]):
        raise ValueError("Current password is incorrect")
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password": hash_password(new_password), "updated_at": datetime.now(timezone.utc)}},
    )
    return True
