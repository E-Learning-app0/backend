from sqlalchemy import Column, ForeignKey, DateTime,Text
from sqlalchemy.orm import relationship
from app.db.session import Base
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

class AlternativeExam(Base):
    __tablename__ = "alternative_exam"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    module_id = Column(UUID(as_uuid=True), ForeignKey("module.id"), nullable=False, unique=True)
    content = Column(JSONB, nullable=False) 
    created_at = Column(DateTime, default=datetime.utcnow)
    
    module = relationship("Module", back_populates="alternative_exam")