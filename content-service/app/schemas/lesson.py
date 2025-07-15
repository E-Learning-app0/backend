# app/schemas/lesson.py
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class LessonBase(BaseModel):
    moduleid: UUID
    title: str
    content: Optional[str] = None
    lessontype: Optional[str] = None
    resourceurl: Optional[str] = None
    orderindex: Optional[int] = None

class LessonCreate(LessonBase):
    pass


class LessonUpdate(LessonBase):
    pass

class LessonRead(LessonBase):
    id: UUID
    createdat: datetime

    class Config:
        orm_mode = True
