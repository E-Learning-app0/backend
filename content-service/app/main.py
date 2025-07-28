# app/main.py
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.routers import lessons  # import your lessons router
from app.routers import modules  # import your lessons router
from app.routers import quiz  # import quiz router
from app.routers import vimeo  # import vimeo router
from app.routers import admin  # import admin router
from fastapi.middleware.cors import CORSMiddleware
from app.routers import users_progress, user_lesson_progress
from app.services.quiz_background_service import quiz_background_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting up the application...")
    print("🚀 Starting up the application...")
    
    # Start the background task for quiz generation immediately
    background_task = asyncio.create_task(quiz_background_service.start_background_task())
    logger.info("✅ Background quiz generation task started automatically")
    print("✅ Background quiz generation task started automatically - will check immediately and then every 3 minutes")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down the application...")
    print("🛑 Shutting down the application...")
    quiz_background_service.is_running = False
    background_task.cancel()
    try:
        await background_task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)

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

app.include_router(lessons.router)
app.include_router(modules.router)
app.include_router(quiz.router)
app.include_router(vimeo.router)
app.include_router(admin.router)
app.include_router(users_progress.router)
app.include_router(user_lesson_progress.router)