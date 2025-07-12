from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserCreate, UserLogin, UserRead, OAuthData
from app.services.auth import hash_password, verify_password, create_access_token
from app.crud.user import get_user_by_email, create_user, get_or_create_fournisseur,get_user_by_id
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

router = APIRouter()
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
    token = create_access_token({"sub": str(user.id)})
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
            user = Utilisateur(
                nom_utilisateur=name,
                email=email,
                mot_de_passe=None,
            )
            user.fournisseurs.append(fournisseur_google)
            db.add(user)
            await db.commit()
            await db.refresh(user)
            is_new_user = True
        else:
            if fournisseur_google not in user.fournisseurs:
                user.fournisseurs.append(fournisseur_google)
            if not user.is_verified:
                user.is_verified = True
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

        token = create_access_token({"sub": str(user.id)})
        return {"access_token": token, "token_type": "bearer"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
