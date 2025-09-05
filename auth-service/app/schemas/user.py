from pydantic import BaseModel, EmailStr
from typing import List, Optional

class UserCreate(BaseModel):
    nom_utilisateur: str
    email: EmailStr
    mot_de_passe: str

class UserLogin(BaseModel):
    email: EmailStr
    mot_de_passe: str

class UserRead(BaseModel):
    id: int
    nom_utilisateur: str
    email: EmailStr

    class Config:
        orm_mode = True


class OAuthData(BaseModel):
    token: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int


# Admin user management schemas
class RoleRead(BaseModel):
    id: int
    nom: str
    
    class Config:
        orm_mode = True

class UserDetailRead(BaseModel):
    id: int
    nom_utilisateur: str
    email: EmailStr
    statut_compte: str
    is_verified: bool
    roles: List[RoleRead] = []
    
    class Config:
        orm_mode = True

class UserCreateByAdmin(BaseModel):
    nom_utilisateur: str
    email: EmailStr
    mot_de_passe: str
    roles: List[str] = []  # Role names
    semester: Optional[str] = None  # For students: S1, S2, S3, S4

class UserUpdateRole(BaseModel):
    role_names: List[str]

class UserUpdate(BaseModel):
    nom_utilisateur: Optional[str] = None
    email: Optional[EmailStr] = None
    statut_compte: Optional[str] = None
    semester: Optional[str] = None

class UserListResponse(BaseModel):
    users: List[UserDetailRead]
    total: int
    page: int
    per_page: int
