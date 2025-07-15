from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime

class TeacherBase(BaseModel):
    external_user_id: UUID
    full_name: str
    email: EmailStr

class TeacherCreate(TeacherBase):
    pass

class TeacherUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None

class TeacherRead(TeacherBase):
    id: UUID
    created_at: datetime

    class Config:
        orm_mode = True
