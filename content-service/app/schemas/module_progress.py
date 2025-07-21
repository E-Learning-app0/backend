# app/schemas/module_progress.py
from pydantic import BaseModel
from uuid import UUID

class ModuleProgressRead(BaseModel):
    module_id: UUID
    module_title: str
    completed_lessons: int
    total_lessons: int
    percent_complete: int
    is_module_unlocked: bool
