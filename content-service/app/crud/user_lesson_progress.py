from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from datetime import datetime
from typing import List
from app.models.user_lesson_progress import UserLessonProgress
from app.schemas.user_lesson_progress import UserLessonProgressCreate, UserLessonProgressUpdate,UserLessonProgressRead


async def get_user_lesson_progress(db: AsyncSession, user_id: int, lesson_id: UUID) -> UserLessonProgress | None:
    stmt = select(UserLessonProgress).where(
        UserLessonProgress.external_user_id == user_id,
        UserLessonProgress.lesson_id == lesson_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_user_lesson_progress(db: AsyncSession, data: UserLessonProgressCreate) -> UserLessonProgress:
    existing = await get_user_lesson_progress(db, data.external_user_id, data.lesson_id)
    if existing:
        return existing
    new_progress = UserLessonProgress(**data.dict())
    db.add(new_progress)
    await db.commit()
    await db.refresh(new_progress)
    return new_progress


async def update_user_lesson_progress(
    db: AsyncSession,
    user_id: int,
    lesson_id: UUID,
    data: UserLessonProgressUpdate
) -> UserLessonProgress:
    progress = await get_user_lesson_progress(db, user_id, lesson_id)
    if not progress:
        return None
    progress.completed = data.completed
    progress.completed_at = datetime.utcnow() if data.completed else None
    if data.score is not None:
        progress.score = data.score
    progress.video_watched = True
    await db.commit()
    await db.refresh(progress)
    return progress


# In your CRUD or service layer (e.g., crud/user_lesson_progress.py)
async def get_user_progress_by_user(
    db: AsyncSession, 
    user_id: str
) -> List[UserLessonProgressRead]:
    result = await db.execute(
        select(UserLessonProgress)
        .where(UserLessonProgress.external_user_id == user_id)
    )
    return result.scalars().all()

async def create_user_lesson_progress(db: AsyncSession, user_id: int, lesson_id: UUID, completed: bool):
    new_progress = UserLessonProgress(
        external_user_id=user_id,
        lesson_id=lesson_id,
        completed=completed,
        
    )
    db.add(new_progress)
    await db.commit()
    await db.refresh(new_progress)
    return new_progress


async def create_user_lesson_progress_v1(db: AsyncSession, user_id: int, lesson_id: UUID, data: UserLessonProgressUpdate):
    new_progress = UserLessonProgress(
        external_user_id=user_id,
        lesson_id=lesson_id,
        completed=data.completed,
        score=data.score,
        video_watched=True,  # Set video_watched
        completed_at=datetime.utcnow() if data.completed else None
    )
    db.add(new_progress)
    await db.commit()
    await db.refresh(new_progress)
    return new_progress

from app.models.module import Module
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.user_progress import UserProgress

async def calculate_module_progress(db: AsyncSession, user_id: UUID):
    # Load all modules and their lessons
    result = await db.execute(
        select(Module).options(selectinload(Module.lessons))
    )
    modules = result.scalars().all()

    # Load all completed lessons for user
    result = await db.execute(
        select(UserLessonProgress).filter(UserLessonProgress.user_id == user_id)
    )
    progress_entries = result.scalars().all()
    completed_lesson_ids = {p.lesson_id for p in progress_entries if p.completed}

    # Load module unlock info from UserProgress table
    result = await db.execute(
        select(UserProgress)
        .filter(UserProgress.external_user_id == user_id)
    )
    progress_per_module = result.scalars().all()
    unlock_status_map = {p.module_id: p.is_module_unlocked for p in progress_per_module}

    # Final result
    module_progress = []
    for module in modules:
        total = len(module.lessons)
        completed = sum(1 for l in module.lessons if l.id in completed_lesson_ids)
        percent = round((completed / total) * 100) if total else 0
        is_unlocked = unlock_status_map.get(module.id, False)

        module_progress.append({
            "module_id": module.id,
            "module_title": module.title,
            "completed_lessons": completed,
            "total_lessons": total,
            "percent_complete": percent,
            "is_module_unlocked": is_unlocked
        })

    return module_progress
