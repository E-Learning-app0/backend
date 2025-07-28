from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import httpx
import os
import jwt
from typing import Optional, Dict, Any

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Configuration - these should match the Auth Service settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")  # Should be same as auth service
ALGORITHM = "HS256"

# Get auth service URL from environment (fallback method)
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8000") + "/api/v1/users/me"

def decode_jwt_locally(token: str) -> Optional[dict]:
    """
    Decode JWT token locally (faster than calling auth service)
    This requires the same SECRET_KEY as the auth service
    Supports both old and new token formats
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check if this is new format (has email and roles) or old format (just sub and exp)
        if "email" in payload and "roles" in payload:
            # New format token
            required_fields = ["sub", "email", "roles", "exp"]
            if not all(field in payload for field in required_fields):
                return None
                
            return {
                "id": payload["sub"],
                "user_id": payload["sub"],
                "email": payload["email"],
                "roles": payload["roles"],
                "exp": payload["exp"],
                "token_format": "new"
            }
        else:
            # Old format token - only has sub and exp
            if "sub" not in payload:
                return None
                
            return {
                "id": payload["sub"],
                "user_id": payload["sub"],
                "email": None,  # Not available in old format
                "roles": [],    # Not available in old format
                "exp": payload["exp"],
                "token_format": "old"
            }
    except jwt.PyJWTError:
        return None

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Get current user info from JWT token.
    First tries local decoding (faster), falls back to auth service if needed.
    """
    # Try local JWT decoding first (faster)
    if SECRET_KEY and SECRET_KEY != "your-secret-key":
        user_info = decode_jwt_locally(token)
        if user_info:
            return user_info
    
    # Fallback to auth service verification
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(AUTH_SERVICE_URL, headers=headers, timeout=10.0)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid credentials"
            )
        
        return response.json()
    
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

def require_role(required_role: str):
    """
    Dependency factory to require specific roles in Content Service.
    Usage: @app.get("/admin-content", dependencies=[Depends(require_role("admin"))])
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
    Dependency factory to require any of the specified roles in Content Service.
    Usage: @app.get("/teacher-content", dependencies=[Depends(require_any_role("teacher", "admin"))])
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
