from pydantic import BaseModel, computed_field, ConfigDict
from typing import Optional, List,Dict
from uuid import UUID
from datetime import datetime
from app.schemas.lesson import LessonRead1, LessonReadSimple,LessonWithProgress

class ModuleBase(BaseModel):
    title: str
    name_fr: Optional[str] = None
    description: Optional[str] = None
    description_fr: Optional[str] = None
    about_en: Optional[str] = None
    about_fr: Optional[str] = None
    image: Optional[str] = None

class ModuleCreate(ModuleBase):
    pass

class ModuleUpdate(BaseModel):
    title: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    semester: Optional[str] = None

class ModuleRead(BaseModel):
    id: UUID
    created_at: datetime
    # other fields...

    model_config = ConfigDict(from_attributes=True)  # Replaces orm_mode=True in Pydantic v2

class ModuleReadWithLessons(BaseModel):
    id: UUID
    title: str
    name_fr: Optional[str] = None
    description: Optional[str] = None
    description_fr: Optional[str] = None
    about_en: Optional[str] = None
    about_fr: Optional[str] = None
    image: Optional[str] = None
    created_at: datetime
    lessons: List[LessonRead1] = []

    model_config = ConfigDict(from_attributes=True)


class ModuleReadCustom(BaseModel):
    id: UUID
    title: str  # Keep original field name from database
    image: Optional[str] = None
    name_fr: Optional[str] = None
    description: Optional[str] = None
    description_fr: Optional[str] = None
    about_en: Optional[str] = None
    about_fr: Optional[str] = None
    semester: Optional[str] = None
    summary_pdf: Optional[str] = None
    lessons: List[LessonReadSimple] = []
    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def name(self) -> str:  # Computed alias for title
        return self.title

    @computed_field
    @property
    def about(self) -> dict:
        return {"en": self.about_en or "", "fr": self.about_fr or ""}
    

class ModuleDetailedResponse(BaseModel):
    id: UUID
    title: str
    lessons: List[LessonWithProgress]
    about: Optional[Dict[str, str]]

class ModuleWithUnlockStatus(BaseModel):
    id: UUID
    title: str
    semester: str
    order: int
    is_unlocked: bool

    class Config:
        orm_mode = True
