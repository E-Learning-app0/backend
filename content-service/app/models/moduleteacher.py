# app/models/moduleteacher.py
import uuid
from sqlalchemy import Column, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base

class ModuleTeacher(Base):
    __tablename__ = "moduleteacher"

    module_id = Column(UUID(as_uuid=True), ForeignKey("module.id"), primary_key=True)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("teacher.id"), primary_key=True)
    assign_date = Column(Date, nullable=False)
    module = relationship("Module", back_populates="module_teachers")
    teacher = relationship("Teacher", back_populates="module_teachers")
