# app/models/session.py
from sqlalchemy import Column, Integer, ForeignKey, String, Boolean
from sqlalchemy.orm import relationship
from db.session import Base

class Session(Base):
    __tablename__ = "session"

    id = Column(Integer, primary_key=True, index=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateur.id", ondelete="CASCADE"), nullable=False)
    jeton_session = Column(String, unique=True, nullable=False)
    adresse_ip = Column(String(45))
    navigateur = Column(String(100))
    est_valide = Column(Boolean, default=True)

    utilisateur = relationship("Utilisateur", back_populates="sessions")
