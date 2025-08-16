from sqlalchemy import Column, ForeignKey, Integer, Float, DateTime,Boolean,String
from sqlalchemy.orm import relationship
from app.db.session import Base
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime

class UserExamResult(Base):
    __tablename__ = "user_exam_result"

    id = Column(Integer, primary_key=True, index=True)
    external_user_id = Column(Integer, nullable=False)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exam.id", ondelete="CASCADE"))
    score = Column(Float)
    status = Column(String)  # e.g. "passed", "failed"
    taken_at = Column(DateTime, default=datetime.utcnow)
    
    # NEW FIELDS for rattrapage
    attempt_number = Column(Integer, default=1)  # 1 = normal, 2 = rattrapage, etc.
    is_retake = Column(Boolean, default=False)   # True if rattrapage
    exams = relationship("Exam", back_populates="user_results")
    
