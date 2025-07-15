from fastapi import Depends, HTTPException
from app.dependencies.auth import get_current_user  # already in your service


def require_any_role(*roles: str):
    def role_checker(user=Depends(get_current_user)):
        if not any(role in user["roles"] for role in roles):
            raise HTTPException(status_code=403, detail="Access forbidden")
        return user
    return role_checker
