from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class LessonFileBase(BaseModel):
    lesson_id: UUID
    filename: str
    file_type: str
    file_url: str

class LessonFileCreate(LessonFileBase):
    pass

class LessonFileUpdate(BaseModel):
    filename: Optional[str] = None
    file_type: Optional[str] = None
    file_url: Optional[str] = None

class LessonFileRead(LessonFileBase):
    id: UUID
    uploaded_at: datetime

    class Config:
        orm_mode = True
