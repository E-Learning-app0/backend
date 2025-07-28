# app/dependencies/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, Any
from app.services.auth import get_user_info_from_token, is_token_new_format

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Dependency to get current user information from JWT token.
    Supports both old format (sub, exp) and new format (sub, email, roles, exp).
    Returns a dict with user_id, email, roles, and exp.
    Can be used by other services as well.
    """
    user_info = get_user_info_from_token(token)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # For old format tokens, roles will be empty and email will be None
    # The frontend should call /token/refresh to upgrade to new format
    return user_info

def require_role(required_role: str):
    """
    Dependency factory to require specific roles.
    Usage: @app.get("/admin", dependencies=[Depends(require_role("admin"))])
    """
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        if required_role not in current_user.get("roles", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return current_user
    return role_checker

def require_any_role(*required_roles: str):
    """
    Dependency factory to require any of the specified roles.
    Usage: @app.get("/content", dependencies=[Depends(require_any_role("teacher", "admin"))])
    """
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_roles = current_user.get("roles", [])
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these roles required: {', '.join(required_roles)}"
            )
        return current_user
    return role_checker
