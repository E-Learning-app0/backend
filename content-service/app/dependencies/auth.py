from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import requests

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")  # le token est obtenu via AuthService

AUTH_SERVICE_URL = "http://auth-service:8000/users/me"

def get_current_user(token: str = Depends(oauth2_scheme)):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(AUTH_SERVICE_URL, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    return response.json()
