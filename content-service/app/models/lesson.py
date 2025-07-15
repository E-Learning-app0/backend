import uuid
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base


class Lesson(Base):
    __tablename__ = "lesson"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    moduleid = Column(UUID(as_uuid=True), ForeignKey("module.id"), nullable=False)  # Singulier "module"
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    lessontype = Column(String(50), nullable=True)
    resourceurl = Column(String(500), nullable=True)
    orderindex = Column(Integer, nullable=True)
    createdat = Column(DateTime, default=datetime.utcnow)

    module = relationship("Module", back_populates="lessons")
    files = relationship("LessonFile", back_populates="lesson")
