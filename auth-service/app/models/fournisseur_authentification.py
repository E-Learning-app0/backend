# app/models/fournisseur_authentification.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from db.session import Base

class FournisseurAuthentification(Base):
    __tablename__ = "fournisseur_authentification"

    id = Column(Integer, primary_key=True, index=True)
    nom_fournisseur = Column(String(100), nullable=False)
    type_fournisseur = Column(String(50), nullable=False)

    utilisateurs = relationship(
        "Utilisateur",
        secondary="utilisateur_fournisseur",
        back_populates="fournisseurs"
    )
