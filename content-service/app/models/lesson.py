import uuid
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer,Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base


class Lesson(Base):
    __tablename__ = "lesson"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    moduleid = Column(UUID(as_uuid=True), ForeignKey("module.id"), nullable=False)  # Singulier "module"
    title = Column(String(255), nullable=False)
    title_fr = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    video = Column(String, nullable=True)  # <- required
    pdf = Column(String, nullable=True) 
    orderindex = Column(Integer, nullable=True)
    createdat = Column(DateTime, default=datetime.utcnow)
    completed = Column(Boolean, default=False, nullable=False)
    module = relationship("Module", back_populates="lessons")
    files = relationship("LessonFile", back_populates="lesson")
