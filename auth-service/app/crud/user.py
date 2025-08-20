# app/crud/user.py
from typing import Optional, List
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.utilisateur import Utilisateur
from app.schemas.user import UserCreate
from sqlalchemy.orm import selectinload
async def get_user_by_email(db: AsyncSession, email: str) -> Optional[Utilisateur]:
    query = select(Utilisateur).options(selectinload(Utilisateur.roles)).where(Utilisateur.email == email)
    result = await db.execute(query)
    user = result.scalars().first()
    
    # DEBUG: Print user roles after loading
    if user:
        print(f"DEBUG CRUD - User {user.id} loaded with {len(user.roles)} roles")
        for role in user.roles:
            print(f"DEBUG CRUD - Role: {role.id} - {role.nom}")
    
    return user

async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[Utilisateur]:
    user_id_int = int(user_id)
    query = select(Utilisateur).options(selectinload(Utilisateur.roles)).filter(Utilisateur.id == user_id_int)
    result = await db.execute(query)
    return result.scalars().first()

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100, role_filter: str = None) -> List[Utilisateur]:
    query = select(Utilisateur).options(selectinload(Utilisateur.roles))
    
    if role_filter:
        # Join with roles table to filter by role
        from app.models.role import Role
        from app.models.links import utilisateur_role
        query = query.join(utilisateur_role).join(Role).filter(Role.nom == role_filter)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

async def get_users_count(db: AsyncSession, role_filter: str = None) -> int:
    query = select(Utilisateur)
    
    if role_filter:
        from app.models.role import Role
        from app.models.links import utilisateur_role
        query = query.join(utilisateur_role).join(Role).filter(Role.nom == role_filter)
    
    result = await db.execute(query)
    return len(result.scalars().all())

async def update_user_roles(db: AsyncSession, user_id: int, role_names: List[str]) -> Optional[Utilisateur]:
    """Update user roles by replacing existing roles with new ones"""
    from app.models.role import Role
    
    user = await get_user_by_id(db, str(user_id))
    if not user:
        return None
    
    # Get role objects by names
    roles_query = select(Role).filter(Role.nom.in_(role_names))
    roles_result = await db.execute(roles_query)
    new_roles = roles_result.scalars().all()
    
    # Replace user's roles
    user.roles = new_roles
    await db.flush()
    
    return user

async def update_user_status(db: AsyncSession, user_id: int, statut_compte: str) -> Optional[Utilisateur]:
    """Update user account status (active, blocked, etc.)"""
    user = await get_user_by_id(db, str(user_id))
    if not user:
        return None
    
    user.statut_compte = statut_compte
    await db.flush()
    return user

async def update_user(db: AsyncSession, user_id: int, user_data: dict) -> Optional[Utilisateur]:
    """Update user information"""
    user = await get_user_by_id(db, str(user_id))
    if not user:
        return None
    
    for field, value in user_data.items():
        if hasattr(user, field) and value is not None:
            setattr(user, field, value)
    
    await db.flush()
    return user

async def delete_user(db: AsyncSession, user_id: int) -> bool:
    """Delete a user"""
    user = await get_user_by_id(db, str(user_id))
    if not user:
        return False
    
    await db.delete(user)
    await db.flush()
    return True

async def create_user_by_admin(db: AsyncSession, user_data: dict, hashed_password: str, role_names: List[str]) -> Utilisateur:
    """Create user with specific roles (admin function)"""
    from app.models.role import Role
    
    # Create the user
    user = Utilisateur(
        nom_utilisateur=user_data["nom_utilisateur"],
        email=user_data["email"],
        mot_de_passe=hashed_password,
        statut_compte="actif",
        is_verified=True  # Admin-created users are auto-verified
    )
    
    # Add roles if specified
    if role_names:
        roles_query = select(Role).filter(Role.nom.in_(role_names))
        roles_result = await db.execute(roles_query)
        roles = roles_result.scalars().all()
        user.roles = roles
    
    db.add(user)
    await db.flush()
    return user

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
