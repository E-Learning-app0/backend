# app/models/teacher.py
import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base
class Teacher(Base):
    __tablename__ = "teacher"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    external_user_id = Column(UUID(as_uuid=True), nullable=False)  # from Auth Service
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    module_teachers = relationship("ModuleTeacher", back_populates="teacher")
