# app/routers/quiz.py
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from app.services.quiz_background_service import quiz_background_service
from app.dependencies.roles import require_any_role
from app.core.quiz_config import quiz_config

router = APIRouter(prefix="/quiz", tags=["Quiz Background Tasks"])
logger = logging.getLogger(__name__)

@router.post("/start-background-task")
async def start_background_quiz_generation(
    background_tasks: BackgroundTasks,
    user=Depends(require_any_role("admin"))
):
    """
    Start the background task for quiz generation.
    Note: The task should already be running automatically on app startup.
    This endpoint is for manual restart if needed.
    """
    if quiz_background_service.is_running:
        raise HTTPException(status_code=400, detail="Background task is already running automatically")
    
    # Start the task in the background
    background_tasks.add_task(quiz_background_service.start_background_task)
    print("🚀 MANUALLY STARTING background task...")
    logger.info("🚀 MANUALLY STARTING background task...")
    return {"message": "Background quiz generation task started manually (should normally start automatically)"}

@router.post("/process-now")
async def process_lessons_now(
    user=Depends(require_any_role("admin"))
):
    """
    Manually trigger quiz generation for all lessons without quiz_id.
    This is useful for immediate processing or testing.
    """
    try:
        success = await quiz_background_service.process_now()
        if success:
            return {"message": "Lessons processed successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to process lessons")
    except Exception as e:
        logger.error(f"Error in manual processing: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process lessons")

@router.get("/task-status")
async def get_task_status(
    user=Depends(require_any_role("admin", "teacher"))
):
    """
    Get the status of the background quiz generation task.
    """
    interval_minutes = quiz_config.QUIZ_GENERATION_INTERVAL_HOURS * 60
    return {
        "is_running": quiz_background_service.is_running,
        "message": "Background task is running automatically" if quiz_background_service.is_running else "Background task is NOT running (should start automatically)",
        "microservice_url": quiz_config.QUIZ_MICROSERVICE_URL,
        "interval_hours": quiz_config.QUIZ_GENERATION_INTERVAL_HOURS,
        "interval_minutes": interval_minutes,
        "test_mode": interval_minutes < 60,
        "note": "Running in TEST MODE (3 minutes) - AUTOMATIC STARTUP" if interval_minutes < 60 else "Running in PRODUCTION MODE - AUTOMATIC STARTUP",
        "startup": "Task starts automatically when application starts and runs immediately + every 3 minutes"
    }

@router.post("/stop-background-task")
async def stop_background_task(
    user=Depends(require_any_role("admin"))
):
    """
    Stop the background quiz generation task.
    """
    if not quiz_background_service.is_running:
        raise HTTPException(status_code=400, detail="Background task is not running")
    
    quiz_background_service.is_running = False
    return {"message": "Background task stop signal sent"}

@router.get("/debug-info")
async def debug_info():
    """
    Debug endpoint to check configuration and service status (no auth for testing)
    """
    return {
        "service_running": quiz_background_service.is_running,
        "config_interval_hours": quiz_config.QUIZ_GENERATION_INTERVAL_HOURS,
        "config_interval_seconds": quiz_config.QUIZ_GENERATION_INTERVAL_HOURS * 60 * 60,
        "microservice_url": quiz_config.QUIZ_MICROSERVICE_URL,
        "pdf_base_url": quiz_config.PDF_BASE_URL,
        "timeout": quiz_config.HTTP_TIMEOUT_SECONDS,
        "debug_note": "PDF filenames will be prefixed with pdf_base_url to create full URLs",
        "example": f"'modelisation_avancee.pdf' becomes '{quiz_config.PDF_BASE_URL}modelisation_avancee.pdf'"
    }
