from datetime import datetime, timedelta
from typing import Optional, List
from passlib.context import CryptContext
import jwt  # PyJWT
from app.core.config import settings  # To get SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# 1. Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 2. Hash password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# 3. Verify password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "token_type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a long-lived refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "token_type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_access_token_for_user(user_id: str, email: str, roles: List[str], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT token with user ID, email, and roles"""
    to_encode = {
        "sub": user_id,
        "user_id": user_id,  # For backward compatibility
        "email": email,
        "roles": roles,
        "token_format": "new"
    }
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "token_type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token_for_user(user_id: str, email: str, roles: List[str], expires_delta: Optional[timedelta] = None) -> str:
    """Create long-lived refresh token with user information"""
    to_encode = {
        "sub": user_id,
        "user_id": user_id,
        "email": email,
        "roles": roles,
        "token_format": "new"
    }
    expire = datetime.utcnow() + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "token_type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_token_pair(user_id: str, email: str, roles: List[str]) -> dict:
    """Create both access and refresh tokens for a user"""
    access_token = create_access_token_for_user(user_id, email, roles)
    refresh_token = create_refresh_token_for_user(user_id, email, roles)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
        "refresh_expires_in": settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # seconds
    }

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

def decode_refresh_token(token: str) -> Optional[dict]:
    """Decode and validate refresh token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # Verify it's actually a refresh token
        if payload.get("token_type") != "refresh":
            return None
        return payload
    except jwt.PyJWTError:
        return None

def verify_token_type(token: str, expected_type: str) -> bool:
    """Verify that the token is of the expected type (access or refresh)"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("token_type") == expected_type
    except jwt.PyJWTError:
        return False

def get_user_info_from_token(token: str) -> Optional[dict]:
    """Extract user information from JWT token"""
    payload = decode_access_token(token)
    if not payload:
        return None
    
    # Check if this is a new-format token with email and roles
    if "email" in payload and "roles" in payload:
        # New format token
        required_fields = ["sub", "email", "roles", "exp"]
        if not all(field in payload for field in required_fields):
            return None
        
        return {
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
            "user_id": payload["sub"],
            "email": None,  # Not available in old format
            "roles": [],    # Not available in old format
            "exp": payload["exp"],
            "token_format": "old"
        }

def is_token_new_format(token: str) -> bool:
    """Check if token has the new format with email and roles"""
    payload = decode_access_token(token)
    if not payload:
        return False
    return "email" in payload and "roles" in payload

