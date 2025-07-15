from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, DateTime,Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.db.session import Base
import uuid

class Module(Base):
    __tablename__ = "module"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    title = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    semester = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    lessons = relationship("Lesson", back_populates="module")
    module_teachers = relationship("ModuleTeacher", back_populates="module")
