from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Gateway settings
    APP_NAME: str = "E-Learning API Gateway"
    DEBUG: bool = False
    
    # Service URLs - can be overridden via environment variables
    AUTH_SERVICE_URL: str = "http://localhost:8000"
    CONTENT_SERVICE_URL: str = "http://localhost:8080"
    
    # Health check settings
    HEALTH_CHECK_TIMEOUT: int = 5  # seconds
    WARMUP_INTERVAL: int = 180  # 3 minutes in seconds
    
    class Config:
        env_file = ".env"

settings = Settings()
