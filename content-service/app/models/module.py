from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, DateTime,Text,Integer
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
# Nouveaux champs
    image = Column(String(255), nullable=True)          # chemin ou url image
    name_fr = Column(String(255), nullable=True)        # nom français
    description_fr = Column(Text, nullable=True)        # description française
    about_en = Column(Text, nullable=True)               # texte about en anglais
    about_fr = Column(Text, nullable=True)               # texte about en français
    order = Column(Integer, nullable=False)

    lessons = relationship("Lesson", back_populates="module")
    
    user_progresses = relationship("UserProgress", back_populates="module",cascade="all, delete-orphan")
    module_teachers = relationship("ModuleTeacher", back_populates="module")
    exams = relationship("Exam", back_populates="module", cascade="all, delete-orphan")
