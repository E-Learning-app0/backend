# app/models/jeton_reinitialisation.py
from sqlalchemy import Column, Integer, ForeignKey, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from db.session import Base

class JetonReinitialisation(Base):
    __tablename__ = "jeton_reinitialisation"

    id = Column(Integer, primary_key=True, index=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateur.id", ondelete="CASCADE"), nullable=False)
    jeton = Column(Text, nullable=False)
    date_expiration = Column(TIMESTAMP, nullable=False)

    utilisateur = relationship("Utilisateur", back_populates="jetons_reinitialisation")
