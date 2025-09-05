from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # JWT Configuration
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Short-lived access token
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7     # Long-lived refresh token (7 days)
    
    # Database Configuration
    DATABASE_URL: str
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: str
    
    # Email Configuration
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int = 587
    MAIL_SERVER: str
    MAIL_TLS: bool = True
    MAIL_SSL: bool = False
    
    # Application URLs
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"
    
    # Service discovery - internal service URLs
    CONTENT_SERVICE_URL: Optional[str] = "http://localhost:8002"
    PAYMENT_SERVICE_URL: Optional[str] = "http://localhost:8005"

    class Config:
        env_file = ".env"

settings = Settings()
