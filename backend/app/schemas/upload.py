from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class FileCategory(str, Enum):
    DOCUMENT = "document"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class UploadedFileResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    category: FileCategory
    url: str
    uploaded_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class UploadListResponse(BaseModel):
    items: list[UploadedFileResponse]
    total: int
    page: int
    page_size: int
