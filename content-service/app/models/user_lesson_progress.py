# app/models/user_lesson_progress.py
from sqlalchemy import Column, Boolean, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.session import Base

class UserLessonProgress(Base):
    __tablename__ = "user_lesson_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_user_id = Column(Integer, nullable=False)  # Comes from Auth Service
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lesson.id"), nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    lesson = relationship("Lesson", back_populates="progress")
    
