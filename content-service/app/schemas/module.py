from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class ModuleBase(BaseModel):
    title: str
    code: str
    description: Optional[str] = None
    semester: str

class ModuleCreate(ModuleBase):
    pass

class ModuleUpdate(BaseModel):
    title: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    semester: Optional[str] = None

class ModuleRead(ModuleBase):
    id: UUID
    created_at: datetime

    class Config:
        orm_mode = True
