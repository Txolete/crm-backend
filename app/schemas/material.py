from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class MaterialResponse(BaseModel):
    id: str
    name: str
    name_slug: str
    version: str
    usage_note: Optional[str] = None
    file_name: str
    mime_type: str
    file_size: int
    status: str
    uploaded_by_user_id: Optional[str] = None
    uploaded_by_name: Optional[str] = None
    uploaded_at: datetime
    retired_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MaterialListResponse(BaseModel):
    materials: List[MaterialResponse]
    total: int


class MaterialUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    usage_note: Optional[str] = Field(None, max_length=1000)
    version: Optional[str] = Field(None, min_length=1, max_length=50)
