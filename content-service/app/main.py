# app/main.py
import asyncio
import logging
import time
import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.routers import lessons  # import your lessons router
from app.routers import modules  # import your lessons router
from app.routers import quiz  # import quiz router
from app.routers import resolution  # import quiz router
from app.routers import vimeo  # import vimeo router
from app.routers import videos  # import unified videos router
from app.routers import apivideo  # import apivideo router
from app.routers import admin  # import admin router
from app.routers import exams  # import admin router
from app.routers import alternative_exams  # import admin router
from app.routers import users_progress, user_lesson_progress
from app.services.quiz_background_service import quiz_background_service
from app.db.session import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="E-Learning Content Service", 
    description="Content management and quiz generation service",
    version="1.0.0"
)

# =================== HEALTH CHECK ENDPOINTS ===================

@app.get("/health")
async def health_check():
    """
    Basic health check endpoint to prevent cold starts.
    Can be called without authentication every 2-3 minutes.
    """
    return {
        "status": "healthy",
        "service": "content-service",
        "version": "1.0.0",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "uptime": time.time()
    }

@app.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """
    Detailed health check that includes database connectivity.
    Use this for thorough monitoring.
    """
    start_time = time.time()
    
    # Test database connection
    db_status = "healthy"
    db_response_time = 0
    try:
        db_start = time.time()
        await db.execute("SELECT 1")
        db_response_time = round((time.time() - db_start) * 1000, 2)  # ms
    except Exception as e:
        db_status = "unhealthy"
        db_response_time = -1
    
    total_response_time = round((time.time() - start_time) * 1000, 2)
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "service": "content-service", 
        "version": "1.0.0",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "checks": {
            "database": {
                "status": db_status,
                "response_time_ms": db_response_time
            }
        },
        "response_time_ms": total_response_time
    }

app.include_router(lessons.router)
app.include_router(modules.router)
app.include_router(quiz.router)
app.include_router(videos.router)  # Unified video service
app.include_router(vimeo.router)   # Legacy Vimeo support
app.include_router(apivideo.router)
app.include_router(admin.router)
app.include_router(exams.router)
app.include_router(users_progress.router)
app.include_router(user_lesson_progress.router)
app.include_router(alternative_exams.router)
app.include_router(resolution.router)