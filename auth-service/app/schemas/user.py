from pydantic import BaseModel, EmailStr

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


from pydantic import BaseModel, EmailStr


class OAuthData(BaseModel):
    token: str
