from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class LessonFileBase(BaseModel):
    filename: str
    file_type: str
    file_url: str

class LessonFileCreate(LessonFileBase):
    lesson_id: UUID

class LessonFileUpdate(BaseModel):
    filename: Optional[str] = None
    file_type: Optional[str] = None
    file_url: Optional[str] = None

class LessonFileInDBBase(LessonFileBase):
    id: UUID
    lesson_id: UUID
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class LessonFileRead(LessonFileInDBBase):
    pass

class LessonFileInDB(LessonFileInDBBase):
    pass

