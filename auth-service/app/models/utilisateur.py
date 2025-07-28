from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from db.session import Base
from app.models.links import utilisateur_fournisseur, utilisateur_role  # ✅ Import only once!

class Utilisateur(Base):
    __tablename__ = "utilisateur"

    id = Column(Integer, primary_key=True, index=True)
    nom_utilisateur = Column(String(100), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    mot_de_passe = Column(Text, nullable=True)
    statut_compte = Column(String(50), default="actif")
    is_verified = Column(Boolean, default=False, nullable=False)

    # ✅ Many-to-Many
    fournisseurs = relationship(
        "FournisseurAuthentification",
        secondary=utilisateur_fournisseur,
        back_populates="utilisateurs",
        lazy="selectin"
    )

    roles = relationship(
        "Role",
        secondary=utilisateur_role,
        back_populates="utilisateurs",
        lazy="selectin"
    )

    # ✅ One-to-Many
    sessions = relationship(
        "Session",
        back_populates="utilisateur",
        cascade="all, delete-orphan"
    )
    jetons_reinitialisation = relationship(
        "JetonReinitialisation",
        back_populates="utilisateur",
        cascade="all, delete-orphan"
    )
    journal_audit = relationship(
        "JournalAudit",
        back_populates="utilisateur",
        cascade="all, delete-orphan"
    )
