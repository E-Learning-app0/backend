from sqlalchemy import Column, Boolean, DateTime, ForeignKey,Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base
import uuid

class UserProgress(Base):
    __tablename__ = "user_progress"
    
    external_user_id = Column(Integer, primary_key=True)
    module_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("module.id", ondelete="CASCADE"), 
        primary_key=True
    )
    is_module_unlocked = Column(Boolean, default=False)
    is_module_completed = Column(Boolean, default=False)
    last_accessed = Column(DateTime)
    completed_at = Column(DateTime)
    module = relationship("Module", back_populates="user_progresses")