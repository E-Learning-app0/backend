# app/models/permission.py
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from db.session import Base
from app.models.links import role_permission
class Permission(Base):
    __tablename__ = "permission"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(50), unique=True, nullable=False)
    description = Column(Text)

    roles = relationship(
        "Role",
        secondary=role_permission,
        back_populates="permissions"
    )
