from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime

from typing import List
from app.db.session import get_db
from app.schemas.user_lesson_progress import UserLessonProgressCreate, UserLessonProgressUpdate, UserLessonProgressRead
from app.crud.user_lesson_progress import create_user_lesson_progress, get_user_lesson_progress, update_user_lesson_progress,get_user_progress_by_user,create_user_lesson_progress,calculate_module_progress
from app.api.deps import get_current_user
from app.dependencies.roles import require_any_role

router = APIRouter(prefix="/user-lesson-progress", tags=["UserLessonProgress"])


@router.post("/", response_model=UserLessonProgressRead, status_code=status.HTTP_201_CREATED)
async def create_progress(
    data: UserLessonProgressCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_any_role("admin", "teacher", "student")),
    current_user: dict = Depends(get_current_user)
):
    existing = await get_user_lesson_progress(db, current_user.id, data.lesson_id)
    if existing:
        return existing

    progress = await create_user_lesson_progress(
        db,
        user_id=current_user.id,
        lesson_id=data.lesson_id,
        completed=False  # si tu veux set ça à False par défaut
    )
    return progress


@router.get("/", response_model=UserLessonProgressRead)
async def read_progress(
    lesson_id: UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_any_role("admin", "teacher", "student")),
    current_user: dict = Depends(get_current_user)
):
    progress = await get_user_lesson_progress(db, current_user.id, lesson_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found")
    return progress


@router.put("/", response_model=UserLessonProgressRead)
async def update_progress(
    lesson_id: UUID,
    data: UserLessonProgressUpdate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_any_role("admin", "teacher", "student")),
    current_user: dict = Depends(get_current_user)
):
    progress = await update_user_lesson_progress(db, current_user.id, lesson_id, data)
    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found")
    return progress


# In your router file (e.g., routers/user_lesson_progress.py)
@router.get("/all", response_model=List[UserLessonProgressRead])
async def get_user_progress(
    db: AsyncSession = Depends(get_db),
    user=Depends(require_any_role("admin", "teacher", "student")),
    current_user: dict = Depends(get_current_user)  # Ensures user is authenticated
):
    """
    Get all lesson progress records for the current user
    Returns records from user_lesson_progress table
    """
    return await get_user_progress_by_user(db, current_user.id)

from app.schemas.module_progress import ModuleProgressRead

@router.get("/modules-progress", response_model=List[ModuleProgressRead])
async def get_modules_progress(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    user=Depends(require_any_role("admin", "teacher", "student"))
):
    """
    Get % progress for each module (based on lesson completion)
    """
    return await calculate_module_progress(db, current_user.id)