from fastapi import APIRouter, Depends, UploadFile, File, status, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.database import get_db
from app.schemas.upload import UploadedFileResponse, UploadListResponse
from app.schemas.common import APIResponse
from app.services.upload_service import save_upload, get_user_uploads, delete_upload
from app.api.dependencies import get_current_user

router = APIRouter()


@router.post("/", response_model=UploadedFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await save_upload(db, file, current_user["id"])


@router.get("/", response_model=UploadListResponse)
async def list_uploads(
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20
    return await get_user_uploads(db, current_user["id"], page, page_size)


@router.delete("/{file_id}", response_model=APIResponse)
async def remove_upload(
    file_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    deleted = await delete_upload(db, file_id, current_user["id"])
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return {"success": True, "message": "File deleted successfully"}
