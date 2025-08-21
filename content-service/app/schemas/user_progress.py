from pydantic import BaseModel,ConfigDict
from datetime import datetime
from typing import Optional
import uuid
from .module import ModuleRead
from uuid import UUID

class UserProgressBase(BaseModel):
    external_user_id: int
    module_id: uuid.UUID

class UserProgressCreate(UserProgressBase):
    is_module_unlocked: bool = False

class UserProgressUpdate(BaseModel):
    is_module_unlocked: Optional[bool] = None
    is_module_completed: Optional[bool] = None
    last_accessed: Optional[datetime] = None
    progress_percentage: Optional[int] = None

class UserProgress(UserProgressBase):
    is_module_unlocked: bool
    is_module_completed: bool
    last_accessed: Optional[datetime]
    completed_at: Optional[datetime]
    progress_percentage: int = 0

    class Config:
        orm_mode = True


class UserProgressWithModule(UserProgress):
    module: ModuleRead  # Nested module data
    
    model_config = ConfigDict(from_attributes=True)

class ModuleWithUnlockStatus(BaseModel):
    id: UUID
    title: str
    semester: str
    is_module_unlocked: bool = False
    progress_percentage: int = 0
    is_completed: bool = False

    class Config:
        orm_mode = True


class SemesterProgressStats(BaseModel):
    completed_modules: int
    total_modules: int
    completion_percentage: float
    is_completed: bool
    is_accessible: bool


class DashboardProgress(BaseModel):
    total_modules_completed: int
    total_modules: int
    semester_stats: dict
    current_semester: str