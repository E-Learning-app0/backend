from fastapi import FastAPI
from app.api.v1.routes import router as auth_router

app = FastAPI(
    title="E-Learning Auth Service",
    description="Authentication and user management service",
    version="1.0.0"
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "auth-service",
        "version": "1.0.0"
    }

app.include_router(auth_router, prefix="/api/v1")
