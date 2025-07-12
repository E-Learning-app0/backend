from sqlalchemy import Table, Column, Integer, ForeignKey
from db.session import Base

utilisateur_fournisseur = Table(
    "utilisateur_fournisseur",
    Base.metadata,
    Column("utilisateur_id", Integer, ForeignKey("utilisateur.id", ondelete="CASCADE"), primary_key=True),
    Column("fournisseur_id", Integer, ForeignKey("fournisseur_authentification.id", ondelete="CASCADE"), primary_key=True)
)

utilisateur_role = Table(
    "utilisateur_role",
    Base.metadata,
    Column("utilisateur_id", Integer, ForeignKey("utilisateur.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("role.id", ondelete="CASCADE"), primary_key=True)
)

role_permission = Table(
    "role_permission",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("role.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permission.id", ondelete="CASCADE"), primary_key=True)
)
