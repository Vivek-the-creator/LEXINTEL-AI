from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.database import get_db
from app.schemas.user import UserResponse, UpdateProfileRequest, ChangePasswordRequest
from app.schemas.common import APIResponse
from app.services.user_service import update_user, change_user_password
from app.api.dependencies import get_current_user

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: dict = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    data: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    updates = data.model_dump(exclude_none=True)
    return await update_user(db, current_user["id"], updates)


@router.post("/me/change-password", response_model=APIResponse)
async def change_password(
    data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    await change_user_password(db, current_user["id"], data.current_password, data.new_password)
    return {"success": True, "message": "Password changed successfully"}
