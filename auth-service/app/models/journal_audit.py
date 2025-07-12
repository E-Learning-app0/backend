# app/models/journal_audit.py
from sqlalchemy import Column, Integer, ForeignKey, String, TIMESTAMP, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.session import Base

class JournalAudit(Base):
    __tablename__ = "journal_audit"

    id = Column(Integer, primary_key=True, index=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateur.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(100), nullable=False)
    horodatage = Column(TIMESTAMP, server_default=func.now())
    details = Column(Text)

    utilisateur = relationship("Utilisateur", back_populates="journal_audit")
