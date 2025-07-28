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
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_access_token_for_user(user_id: str, email: str, roles: List[str], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT token with user ID, email, and roles"""
    to_encode = {
        "sub": user_id,
        "email": email,
        "roles": roles
    }
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

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

