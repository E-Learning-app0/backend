# app/crud/user.py
from typing import Optional, List
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.utilisateur import Utilisateur
from app.schemas.user import UserCreate
from sqlalchemy.orm import selectinload
async def get_user_by_email(db: AsyncSession, email: str) -> Optional[Utilisateur]:
    result = await db.execute(select(Utilisateur).where(Utilisateur.email == email))
    return result.scalars().first()

async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[Utilisateur]:
    user_id_int = int(user_id)
    query = select(Utilisateur).options(selectinload(Utilisateur.roles)).filter(Utilisateur.id == user_id_int)
    result = await db.execute(query)
    return result.scalars().first()

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Utilisateur]:
    result = await db.execute(select(Utilisateur).offset(skip).limit(limit))
    return result.scalars().all()

async def create_user(db: AsyncSession, user_in: UserCreate, hashed_password: str) -> Utilisateur:
    user = Utilisateur(
        nom_utilisateur = user_in.nom_utilisateur,
        email=user_in.email,
        mot_de_passe=hashed_password,
        statut_compte="ACTIF",  # or False, depending on your logic
    )
    db.add(user)
    await db.flush()  # flush so that SQLAlchemy assigns ID, if needed
    return user


from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.fournisseur_authentification import FournisseurAuthentification

async def get_fournisseur_by_name(db: AsyncSession, nom_fournisseur: str) -> FournisseurAuthentification | None:
    result = await db.execute(select(FournisseurAuthentification).filter(FournisseurAuthentification.nom_fournisseur == nom_fournisseur))
    return result.scalars().first()

async def create_fournisseur(db: AsyncSession, nom_fournisseur: str, type_fournisseur: str) -> FournisseurAuthentification:
    fournisseur = FournisseurAuthentification(nom_fournisseur=nom_fournisseur, type_fournisseur=type_fournisseur)
    db.add(fournisseur)
    await db.flush()
    return fournisseur

async def get_or_create_fournisseur(db: AsyncSession, nom_fournisseur: str, type_fournisseur: str) -> FournisseurAuthentification:
    fournisseur = await get_fournisseur_by_name(db, nom_fournisseur)
    if fournisseur:
        return fournisseur
    return await create_fournisseur(db, nom_fournisseur, type_fournisseur)
