from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class UserLessonProgressBase(BaseModel):
    external_user_id: int
    lesson_id: UUID

class UserLessonProgressCreate(BaseModel):
    lesson_id: UUID

class UserLessonProgressUpdate(BaseModel):
    completed: bool

class UserLessonProgressRead(UserLessonProgressBase):
    completed: bool
    completed_at: Optional[datetime]

    class Config:
        orm_mode = True
