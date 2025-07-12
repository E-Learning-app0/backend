# app/models/role.py
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from db.session import Base
from app.models.links import utilisateur_role, role_permission

class Role(Base):
    __tablename__ = "role"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(50), unique=True, nullable=False)
    description = Column(Text)

    utilisateurs = relationship(
        "Utilisateur",
        secondary=utilisateur_role,
        back_populates="roles"
    )
    permissions = relationship(
        "Permission",
        secondary=role_permission,
        back_populates="roles"
    )
