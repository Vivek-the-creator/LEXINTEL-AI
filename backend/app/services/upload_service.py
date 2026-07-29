import os
import uuid
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import aiofiles

from app.core.config import settings
from app.schemas.upload import FileCategory

MIME_TO_CATEGORY = {
    "application/pdf": FileCategory.DOCUMENT,
    "image/": FileCategory.IMAGE,
    "audio/": FileCategory.AUDIO,
    "video/": FileCategory.VIDEO,
}

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png", "image/jpeg", "image/gif", "image/webp",
    "audio/mpeg", "audio/wav", "audio/ogg",
    "video/mp4", "video/avi", "video/quicktime", "video/x-matroska",
}


def _get_category(mime_type: str) -> FileCategory:
    for prefix, category in MIME_TO_CATEGORY.items():
        if mime_type.startswith(prefix):
            return category
    return FileCategory.DOCUMENT


def _serialize_file(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


async def save_upload(
    db: AsyncIOMotorDatabase, file: UploadFile, user_id: str
) -> dict:
    content = await file.read()

    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.MAX_FILE_SIZE_MB}MB",
        )

    ext = Path(file.filename).suffix.lower().lstrip(".")
    if ext not in settings.allowed_extensions_set:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '.{ext}' is not allowed",
        )

    mime_type = file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
    if not any(mime_type.startswith(allowed.split("/")[0]) or mime_type == allowed for allowed in ALLOWED_MIME_TYPES):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File MIME type is not allowed",
        )

    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = Path(settings.UPLOAD_DIR) / unique_filename

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    file_doc = {
        "filename": unique_filename,
        "original_filename": file.filename,
        "file_size": len(content),
        "mime_type": mime_type,
        "category": _get_category(mime_type).value,
        "file_path": str(file_path),
        "url": f"/uploads/{unique_filename}",
        "uploaded_by": user_id,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.uploads.insert_one(file_doc)
    file_doc["_id"] = result.inserted_id
    return _serialize_file(file_doc)


async def get_user_uploads(
    db: AsyncIOMotorDatabase, user_id: str, page: int = 1, page_size: int = 20
) -> dict:
    skip = (page - 1) * page_size
    cursor = db.uploads.find({"uploaded_by": user_id}).sort("created_at", -1).skip(skip).limit(page_size)
    items = [_serialize_file(doc) async for doc in cursor]
    total = await db.uploads.count_documents({"uploaded_by": user_id})
    return {"items": items, "total": total, "page": page, "page_size": page_size}


async def delete_upload(db: AsyncIOMotorDatabase, file_id: str, user_id: str) -> bool:
    try:
        doc = await db.uploads.find_one({"_id": ObjectId(file_id), "uploaded_by": user_id})
    except Exception:
        return False
    if not doc:
        return False
    file_path = Path(doc.get("file_path", ""))
    if file_path.exists():
        file_path.unlink()
    await db.uploads.delete_one({"_id": ObjectId(file_id)})
    return True
