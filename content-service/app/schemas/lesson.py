from pydantic import BaseModel,ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime


class LessonBase(BaseModel):
    moduleid: UUID
    title: str
    content: Optional[str] = None
    title_fr: Optional[str] = None
    resourceurl: Optional[str] = None
    orderindex: Optional[int] = None
    completed: Optional[bool] = False
    video: Optional[str] = None
    vimeo_id: Optional[str] = None
    video_type: Optional[str] = None

class LessonCreate(LessonBase):
    pass

class LessonUpdate(LessonBase):
    pass

class LessonOrderUpdate(BaseModel):
    orderindex: int
    
    class Config:
        schema_extra = {
            "example": {"orderindex": 1}
        }

class LessonRead(LessonBase):
    id: UUID
    createdat: datetime

    class Config:
        orm_mode = True

class LessonRead1(BaseModel):
    id: UUID
    moduleid: UUID
    title: str
    content: Optional[str]
    title_fr: Optional[str]
    resourceurl: Optional[str]
    orderindex: Optional[int]
    completed: bool
    video: Optional[str]
    pdf: Optional[str]
    createdat: datetime
    vimeo_id: Optional[str] = None
    video_type: Optional[str] = None

    class Config:
        orm_mode = True


# Si tu souhaites garder la classe fichiers pour d'autres usages, tu peux la conserver
class LessonFileRead(BaseModel):
    id: UUID
    lesson_id: UUID
    filename: str
    file_type: str
    file_url: str
    uploaded_at: datetime

    class Config:
        orm_mode = True


# Tu peux supprimer LessonReadWithLessons si tu ne veux plus renvoyer la liste files
# ou la garder pour un autre usage spécifique


class LessonReadSimple(BaseModel):
    id: UUID
    title: str
    title_fr: Optional[str]
    video: Optional[str]
    pdf: Optional[str]
    completed: bool
    quiz_id: Optional[str] = None
    orderindex: Optional[int] = None
    vimeo_id: Optional[str] = None
    video_type: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class LessonWithProgress(BaseModel):
    id: UUID
    title: str
    completed: bool
