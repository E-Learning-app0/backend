from sqlalchemy import Column, String, DateTime, Integer,ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base
import uuid
from sqlalchemy.dialects.postgresql import JSONB

class Exam(Base):
    __tablename__ = "exam"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    content = Column(JSONB, nullable=True)
    scheduled_date = Column(DateTime, nullable=True)     # date de l'examen, si fixe
    duration_minutes = Column(Integer, nullable=True)    # durée (ex: 90)
    
    module_id = Column(
        UUID(as_uuid=True),
        ForeignKey("module.id", ondelete="CASCADE"),
        nullable=False
    )

    # Relationships
    module = relationship("Module", back_populates="exams")
    user_results = relationship("UserExamResult", back_populates="exams", cascade="all, delete")
