from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer
from app.schemas.user import UserCreate, UserLogin, UserRead, OAuthData
from app.services.auth import hash_password, verify_password, create_access_token,decode_access_token, create_access_token_for_user
from app.crud.user import get_user_by_email, create_user, get_or_create_fournisseur,get_user_by_id,get_role_by_name
from db.session import get_db
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.models.utilisateur import Utilisateur
from app.services.auth import create_access_token
from app.services.audit import log_action
from pydantic import BaseModel
from app.core.config import settings
from app.crud.verification import get_verification_by_token
from app.crud.verification import  get_verification_by_token, save_verification_token
import uuid
from app.services.email import send_verification_email
from app.dependencies.auth import get_current_user, require_role, require_any_role
from typing import Dict, Any


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.get("/users/me")
async def read_users_me(current_user: Dict[str, Any] = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get current user information from JWT token"""
    # We can get most info directly from JWT, but still need DB for some fields like is_verified
    user = await get_user_by_id(db, current_user["user_id"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return {
        "id": current_user["user_id"],
        "email": current_user["email"],
        "is_verified": user.is_verified,
        "full_name": user.nom_utilisateur,
        "roles": current_user["roles"]
    }

@router.get("/token/info")
async def get_token_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get information directly from JWT token (no database query needed)"""
    return {
        "user_id": current_user["user_id"],
        "email": current_user["email"], 
        "roles": current_user["roles"],
        "token_expires": current_user["exp"],
        "token_format": current_user.get("token_format", "unknown")
    }

@router.post("/refresh")
async def refresh_token(current_user: Dict[str, Any] = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Refresh token and upgrade to new format if needed.
    Critical endpoint to prevent users from being logged out.
    Accepts refresh tokens via Authorization Bearer header.
    """
    # If it's already a new format token, just create a new one with fresh expiry
    if current_user.get("token_format") == "new":
        new_token = create_access_token_for_user(
            user_id=current_user["user_id"],
            email=current_user["email"],
            roles=current_user["roles"]
        )
        return {
            "access_token": new_token,
            "token_type": "bearer",
            "message": "Token refreshed successfully"
        }
    
    # For old format tokens, we need to get fresh user data from DB
    user = await get_user_by_id(db, current_user["user_id"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    # Create new format token with email and roles
    role_names = [role.nom for role in user.roles] if user.roles else []
    new_token = create_access_token_for_user(
        user_id=str(user.id),
        email=user.email,
        roles=role_names
    )
    
    await log_action(
        db=db,
        utilisateur_id=user.id,
        action="token_refresh",
        details="Token refreshed and upgraded to new format"
    )
    
    return {
        "access_token": new_token,
        "token_type": "bearer",
        "message": "Token refreshed and upgraded to new format with email and roles"
    }

@router.post("/token/refresh")
async def refresh_token_legacy(current_user: Dict[str, Any] = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Legacy refresh token endpoint - kept for backward compatibility.
    Use /refresh instead.
    """
    # Delegate to the main refresh endpoint
    return await refresh_token(current_user, db)

# Example protected endpoints with role requirements
@router.get("/admin-only")
async def admin_only_endpoint(current_user: Dict[str, Any] = Depends(require_role("admin"))):
    """Example endpoint that requires admin role"""
    return {"message": f"Hello admin {current_user['email']}!", "data": "secret admin data"}

@router.get("/teacher-or-admin")  
async def teacher_or_admin_endpoint(current_user: Dict[str, Any] = Depends(require_any_role("teacher", "admin"))):
    """Example endpoint that requires teacher or admin role"""
    return {"message": f"Hello {current_user['email']}!", "roles": current_user["roles"]}

@router.post("/force-new-token")
async def force_new_token(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Force create new format token - for testing"""
    user = await get_user_by_email(db, credentials.email)

    if not user or not verify_password(credentials.mot_de_passe, user.mot_de_passe):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Force roles even if empty
    role_names = [role.nom for role in user.roles] if user.roles else ["student"]  # Default role
    
    # Create new format token
    token = create_access_token_for_user(
        user_id=str(user.id),
        email=user.email,
        roles=role_names
    )
    
    return {
        "access_token": token, 
        "token_type": "bearer",
        "payload": decode_access_token(token)
    }

@router.get("/debug-user-roles/{user_id}")
async def debug_user_roles(user_id: str, db: AsyncSession = Depends(get_db)):
    """Debug endpoint to check user's roles via direct SQL"""
    try:
        # Direct SQL query to check roles
        from sqlalchemy import text
        
        sql_query = text("""
            SELECT u.id as user_id, u.email, r.id as role_id, r.nom as role_name
            FROM utilisateur u
            LEFT JOIN utilisateur_role ur ON u.id = ur.utilisateur_id  
            LEFT JOIN role r ON ur.role_id = r.id
            WHERE u.id = :user_id
        """)
        
        result = await db.execute(sql_query, {"user_id": int(user_id)})
        rows = result.fetchall()
        
        return {
            "user_id": user_id,
            "raw_sql_result": [
                {
                    "user_id": row.user_id,
                    "email": row.email, 
                    "role_id": row.role_id,
                    "role_name": row.role_name
                } for row in rows
            ],
            "roles_count": len([row for row in rows if row.role_id is not None])
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/debug-user/{user_id}")
async def debug_user(user_id: str, db: AsyncSession = Depends(get_db)):
    """Debug endpoint to check user's roles"""
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user_id": str(user.id),
        "email": user.email,
        "nom_utilisateur": user.nom_utilisateur,
        "roles": [{"id": role.id, "nom": role.nom, "description": role.description} for role in user.roles],
        "roles_count": len(user.roles),
        "has_roles": len(user.roles) > 0
    }

@router.post("/debug-login")
async def debug_login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Debug endpoint to see what's happening during login"""
    user = await get_user_by_email(db, credentials.email)

    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    
    if not verify_password(credentials.mot_de_passe, user.mot_de_passe):
        raise HTTPException(status_code=400, detail="Invalid password")

    # Debug: Check user roles
    role_names = [role.nom for role in user.roles] if user.roles else []
    
    # Create both types of tokens for comparison
    old_token = create_access_token({"sub": str(user.id)})
    new_token = create_access_token_for_user(
        user_id=str(user.id),
        email=user.email,
        roles=role_names
    )
    
    return {
        "user_info": {
            "id": str(user.id),
            "email": user.email,
            "roles": role_names,
            "roles_count": len(role_names)
        },
        "old_token": old_token,
        "new_token": new_token,
        "old_payload": decode_access_token(old_token),
        "new_payload": decode_access_token(new_token)
    }




@router.get("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    verification = await get_verification_by_token(db, token)
    if not verification:
        raise HTTPException(status_code=400, detail="Token invalide ou expiré")

    user = await get_user_by_id(db, verification.utilisateur_id)
    user.is_verified = True
    db.add(user)
    await db.delete(verification) 
    await db.commit()
    await log_action(
        db=db,
        utilisateur_id=user.id,
        action="email_verification",
        details="Utilisateur a vérifié son email avec succès"
    )
    return {"message": "Email vérifié avec succès"}


@router.post("/register", response_model=UserRead)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(user.mot_de_passe)
    new_user = await create_user(db, user, hashed_pw)

    # 🔐 Crée un token unique de vérification
    verification_token = str(uuid.uuid4())

    # Enregistre-le dans une table `email_verification` (à créer)
    await save_verification_token(db, user_id=new_user.id, token=verification_token)

    #verification_link = f"http://localhost:8000/api/v1/verify-email?token={verification_token}"
    FRONTEND_URL = "https://frontend-five-pi-35.vercel.app"

    verification_link = f"{FRONTEND_URL}/verify-email?token={verification_token}"
    await send_verification_email(new_user.email, verification_link)

    await log_action(
        db=db,
        utilisateur_id=new_user.id,
        action="register",
        details="Nouvelle inscription via formulaire classique"
    )

    return new_user

@router.post("/login")
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, credentials.email)

    if not user or not verify_password(credentials.mot_de_passe, user.mot_de_passe):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    await log_action(
        db=db,
        utilisateur_id=user.id,
        action="login",
        details="Connexion avec email et mot de passe"
    )
    
    # Extract user roles - try relationship first, then manual query
    role_names = [role.nom for role in user.roles] if user.roles else []
    
    # If no roles loaded via relationship, try manual query
    if not role_names:
        print("DEBUG - No roles via relationship, trying manual query...")
        from sqlalchemy import text
        role_query = text("""
            SELECT r.nom 
            FROM role r 
            JOIN utilisateur_role ur ON r.id = ur.role_id 
            WHERE ur.utilisateur_id = :user_id
        """)
        role_result = await db.execute(role_query, {"user_id": user.id})
        role_names = [row.nom for row in role_result.fetchall()]
        print(f"DEBUG - Manual query found {len(role_names)} roles: {role_names}")
    
    # DEBUG: Print what we're creating
    print(f"DEBUG - Creating token for user {user.id}")
    print(f"DEBUG - Email: {user.email}")
    print(f"DEBUG - Roles: {role_names}")
    print(f"DEBUG - Roles count: {len(role_names)}")
    
    # Create token with email and roles
    token = create_access_token_for_user(
        user_id=str(user.id),
        email=user.email,
        roles=role_names
    )
    
    # DEBUG: Decode the token to see what was actually created
    decoded = decode_access_token(token)
    print(f"DEBUG - Token payload: {decoded}")
    
    return {"access_token": token, "token_type": "bearer"}


class OAuthToken(BaseModel):
    token: str



from app.services.audit import log_action  # à adapter selon ton arborescence

@router.post("/oauth-login")
async def oauth_login(oauth_data: OAuthToken, db: AsyncSession = Depends(get_db)):
    try:
        # validation et extraction
        idinfo = id_token.verify_oauth2_token(
            oauth_data.token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )
        email = idinfo.get("email")
        name = idinfo.get("name", "GoogleUser")

        # récupération ou création
        user = await get_user_by_email(db, email)
        fournisseur_google = await get_or_create_fournisseur(db, nom_fournisseur="google", type_fournisseur="oauth")

        is_new_user = False

        if not user:
            default_role = await get_role_by_name(db, "user")
            
            if not default_role:
                raise HTTPException(status_code=500, detail="Default role 'user' not found")
            
            user = Utilisateur(
                nom_utilisateur=name,
                email=email,
                mot_de_passe=None,
                roles=[default_role],
                fournisseurs=[fournisseur_google]
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            is_new_user = True
        else:
            if fournisseur_google not in user.fournisseurs:
                user.fournisseurs.append(fournisseur_google)
            if not user.is_verified:
                user.is_verified = True
                 
            if not user.roles:
                default_role = await get_role_by_name(db, "user")
                if default_role:
                    user.roles.append(default_role)
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # 🔥 journaliser ici
        await log_action(
            db=db,
            utilisateur_id=user.id,
            action="oauth_login",
            details="Connexion avec Google (création de compte)" if is_new_user else "Connexion avec Google"
        )

        # Extract user roles
        role_names = [role.nom for role in user.roles] if user.roles else []
        
        # Create token with email and roles
        token = create_access_token_for_user(
            user_id=str(user.id),
            email=user.email,
            roles=role_names
        )
        return {"access_token": token, "token_type": "bearer"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =================== ADMIN USER MANAGEMENT ENDPOINTS ===================

@router.get("/admin/users", response_model=Dict[str, Any])
async def list_users(
    page: int = 1,
    per_page: int = 20,
    role: str = None,
    current_user: Dict[str, Any] = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """List all users with pagination and optional role filtering"""
    skip = (page - 1) * per_page
    
    # Import here to avoid circular imports
    from app.crud.user import get_users, get_users_count
    
    users = await get_users(db, skip=skip, limit=per_page, role_filter=role)
    total = await get_users_count(db, role_filter=role)
    
    users_data = []
    for user in users:
        user_dict = {
            "id": user.id,
            "nom_utilisateur": user.nom_utilisateur,
            "email": user.email,
            "statut_compte": user.statut_compte,
            "is_verified": user.is_verified,
            "roles": [{"id": r.id, "nom": r.nom} for r in user.roles] if user.roles else []
        }
        users_data.append(user_dict)
    
    return {
        "users": users_data,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }

@router.get("/admin/users/{user_id}")
async def get_user_by_admin(
    user_id: int,
    current_user: Dict[str, Any] = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """Get specific user details"""
    user = await get_user_by_id(db, str(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "nom_utilisateur": user.nom_utilisateur,
        "email": user.email,
        "statut_compte": user.statut_compte,
        "is_verified": user.is_verified,
        "roles": [{"id": r.id, "nom": r.nom} for r in user.roles] if user.roles else []
    }

@router.post("/admin/users")
async def create_user_by_admin(
    user_data: dict,
    current_user: Dict[str, Any] = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user (admin only)"""
    from app.crud.user import create_user_by_admin
    from app.services.auth import hash_password
    
    # Check if user exists
    existing_user = await get_user_by_email(db, user_data["email"])
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Hash password
    hashed_password = hash_password(user_data["mot_de_passe"])
    
    # Extract roles
    role_names = user_data.get("roles", [])
    
    # Create user
    new_user = await create_user_by_admin(
        db=db,
        user_data=user_data,
        hashed_password=hashed_password,
        role_names=role_names
    )
    
    await db.commit()
    
    # Log action
    await log_action(
        db=db,
        utilisateur_id=new_user.id,
        action="user_created_by_admin",
        details=f"User created by admin {current_user['email']} with roles: {role_names}"
    )
    
    return {
        "id": new_user.id,
        "nom_utilisateur": new_user.nom_utilisateur,
        "email": new_user.email,
        "statut_compte": new_user.statut_compte,
        "roles": [{"id": r.id, "nom": r.nom} for r in new_user.roles] if new_user.roles else []
    }

@router.put("/admin/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role_data: dict,
    current_user: Dict[str, Any] = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """Update user roles"""
    from app.crud.user import update_user_roles
    
    role_names = role_data.get("role_names", [])
    
    user = await update_user_roles(db, user_id, role_names)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.commit()
    
    # Log action
    await log_action(
        db=db,
        utilisateur_id=user.id,
        action="user_roles_updated",
        details=f"Roles updated by admin {current_user['email']} to: {role_names}"
    )
    
    return {
        "id": user.id,
        "nom_utilisateur": user.nom_utilisateur,
        "email": user.email,
        "roles": [{"id": r.id, "nom": r.nom} for r in user.roles] if user.roles else []
    }

@router.put("/admin/users/{user_id}")
async def update_user_by_admin(
    user_id: int,
    update_data: dict,
    current_user: Dict[str, Any] = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """Update user information"""
    from app.crud.user import update_user
    
    user = await update_user(db, user_id, update_data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.commit()
    
    # Log action
    await log_action(
        db=db,
        utilisateur_id=user.id,
        action="user_updated_by_admin",
        details=f"User updated by admin {current_user['email']}"
    )
    
    return {
        "id": user.id,
        "nom_utilisateur": user.nom_utilisateur,
        "email": user.email,
        "statut_compte": user.statut_compte,
        "is_verified": user.is_verified,
        "roles": [{"id": r.id, "nom": r.nom} for r in user.roles] if user.roles else []
    }

@router.delete("/admin/users/{user_id}")
async def delete_user_by_admin(
    user_id: int,
    current_user: Dict[str, Any] = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """Delete a user"""
    from app.crud.user import delete_user
    
    # Get user info before deletion for logging
    user = await get_user_by_id(db, str(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admin from deleting themselves
    if str(user.id) == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    success = await delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.commit()
    
    # Log action
    await log_action(
        db=db,
        utilisateur_id=int(current_user["user_id"]),  # Log against admin who performed the action
        action="user_deleted_by_admin",
        details=f"User {user.email} (ID: {user.id}) deleted by admin {current_user['email']}"
    )
    
    return {"message": "User deleted successfully"}

@router.put("/admin/users/{user_id}/block")
async def block_user(
    user_id: int,
    current_user: Dict[str, Any] = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """Block a user account"""
    from app.crud.user import update_user_status
    
    # Prevent admin from blocking themselves
    if str(user_id) == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot block your own account")
    
    user = await update_user_status(db, user_id, "blocked")
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.commit()
    
    # Log action
    await log_action(
        db=db,
        utilisateur_id=user.id,
        action="user_blocked",
        details=f"User blocked by admin {current_user['email']}"
    )
    
    return {"message": "User blocked successfully", "user_id": user.id}

@router.put("/admin/users/{user_id}/unblock")
async def unblock_user(
    user_id: int,
    current_user: Dict[str, Any] = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """Unblock a user account"""
    from app.crud.user import update_user_status
    
    user = await update_user_status(db, user_id, "actif")
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.commit()
    
    # Log action
    await log_action(
        db=db,
        utilisateur_id=user.id,
        action="user_unblocked",
        details=f"User unblocked by admin {current_user['email']}"
    )
    
    return {"message": "User unblocked successfully", "user_id": user.id}

# Additional admin endpoints for dashboard stats
@router.get("/admin/stats/users")
async def get_user_stats(
    current_user: Dict[str, Any] = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """Get user statistics for dashboard"""
    from app.crud.user import get_users_count
    
    total_users = await get_users_count(db)
    students_count = await get_users_count(db, role_filter="student")
    teachers_count = await get_users_count(db, role_filter="teacher")
    admins_count = await get_users_count(db, role_filter="admin")
    
    return {
        "total_users": total_users,
        "students": students_count,
        "teachers": teachers_count,
        "admins": admins_count
    }
