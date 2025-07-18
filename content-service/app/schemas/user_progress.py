from pydantic import BaseModel,ConfigDict
from datetime import datetime
from typing import Optional
import uuid
from .module import ModuleRead


class UserProgressBase(BaseModel):
    external_user_id: int
    module_id: uuid.UUID

class UserProgressCreate(UserProgressBase):
    is_module_unlocked: bool = False

class UserProgressUpdate(BaseModel):
    is_module_unlocked: Optional[bool] = None
    is_module_completed: Optional[bool] = None
    last_accessed: Optional[datetime] = None

class UserProgress(UserProgressBase):
    is_module_unlocked: bool
    is_module_completed: bool
    last_accessed: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        orm_mode = True


class UserProgressWithModule(UserProgress):
    module: ModuleRead  # Nested module data
    
    model_config = ConfigDict(from_attributes=True)