# app/main.py
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.routers import lessons  # import your lessons router
from app.routers import modules  # import your lessons router
from app.routers import exams  # import quiz router
from app.routers import quiz  # import exam router
from app.routers import resolution  # import exam router
from app.routers import vimeo  # import vimeo router
from app.routers import lessonfiles  # import vimeo router
from app.routers import admin  # import admin router
from app.routers import users_progress, user_lesson_progress

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="E-Learning Content Service", 
    description="Content management and quiz generation service",
    version="1.0.0"
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "content-service",
        "version": "1.0.0"
    }

app.include_router(lessons.router)
app.include_router(modules.router)
app.include_router(quiz.router)
app.include_router(exams.router)
app.include_router(vimeo.router)
app.include_router(lessonfiles.router)
app.include_router(admin.router)
app.include_router(resolution.router)
app.include_router(users_progress.router)
app.include_router(user_lesson_progress.router)