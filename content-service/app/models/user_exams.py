from sqlalchemy import Column, ForeignKey, Integer, Float, DateTime, Boolean, String
from sqlalchemy.orm import relationship
from app.db.session import Base
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

class UserExam(Base):
    __tablename__ = "user_exams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    external_user_id = Column(Integer, nullable=False)
    module_id = Column(UUID(as_uuid=True), ForeignKey("module.id", ondelete="CASCADE"))
    
    # Exam content and metadata
    content = Column(JSONB, nullable=False)  # Changed to not nullable
    supabase_urls = Column(JSONB, nullable=True)  # Store the PDF URLs used for generation
    
    # Exam progress and results
    status = Column(String(20), default='generated')  # 'generated', 'in-progress', 'passed', 'failed'
    score = Column(Float, nullable=True)  # Percentage score
    correct_answers = Column(Integer, nullable=True)
    total_questions = Column(Integer, nullable=True)
    time_spent = Column(Integer, nullable=True)  # Seconds
    
    # Retake system
    attempt_number = Column(Integer, default=1)  # 1 = normal, 2 = retake, etc.
    is_retake = Column(Boolean, default=False)
    
    user_answer = Column(JSONB, nullable=False)
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    module = relationship("Module", back_populates="user_exams")