# app/models/verification.py
from sqlalchemy import Column, String, ForeignKey, DateTime, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.session import Base

class EmailVerification(Base):
    __tablename__ = "email_verification"
    token = Column(String, primary_key=True, index=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateur.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    utilisateur = relationship("Utilisateur")
