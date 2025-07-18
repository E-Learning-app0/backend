from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from uuid import UUID
import requests

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class CurrentUser(BaseModel):
    id: int  # Must match your external_user_id type
    email: str
    is_active: bool = True
    roles: list[str] = []

    class Config:
        from_attributes = True  # Pydantic v2 style

async def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    """Returns a typed CurrentUser object, not a dict"""
    try:
        response = requests.get(
            "http://localhost:8000/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        response.raise_for_status()
        user_data = response.json()
        
        # Ensure the ID is an integer
        user_data["id"] = int(user_data["id"])
        
        return CurrentUser(**user_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )