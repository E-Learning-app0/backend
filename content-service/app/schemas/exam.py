# app/schemas/exam.py
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

class ExamBase(BaseModel):
    user_id: int
    module_id: UUID

class ExamCreate(BaseModel):
    module_id: UUID

class ExamUpdate(BaseModel):
    content: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    score: Optional[float] = None
    correct_answers: Optional[int] = None
    time_spent: Optional[int] = None
    supabase_urls: Optional[List[str]] = None

class ExamResponse(ExamBase):
    id: UUID
    score: Optional[float] = None
    status: str
    content: Optional[dict] = None
    correct_answers: Optional[int] = None
    total_questions: Optional[int] = None
    time_spent: Optional[int] = None
    attempt_number: int = 1
    is_retake: bool = False
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    user_answer: Optional[List[Dict]] = None 

    class Config:
        from_attributes = True


class ExamCreatedResponse(BaseModel):
    message: str
    exam_id: UUID
    status: str
    is_retake: bool
    attempt_number: int
    class Config:
        from_attributes = True

        
class ExamResultUpdate(BaseModel):
    score: float
    correct_answers: int
    total_questions: int
    time_spent: int
    status: Optional[str] = "passed"
    user_answer: Optional[List[Dict]] = None 