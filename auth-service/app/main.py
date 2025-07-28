from fastapi import FastAPI
from app.api.v1.routes import router as auth_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="E-Learning Auth Service",
    description="Authentication and user management service",
    version="1.0.0"
)

origins = [
    "http://localhost:5173",  
    "https://frontend-five-pi-35.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            
    allow_credentials=True,
    allow_methods=["*"],              
    allow_headers=["*"],              
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
