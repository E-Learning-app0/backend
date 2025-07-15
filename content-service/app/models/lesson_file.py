import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class LessonFile(Base):
    __tablename__ = "lessonfile"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lesson.id"), nullable=False)  # ✅ corrigé ici
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_url = Column(String(500), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    lesson = relationship("Lesson", back_populates="files")
