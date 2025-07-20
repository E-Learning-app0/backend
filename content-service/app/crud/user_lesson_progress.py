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

async def create_user_lesson_progress(db: AsyncSession, user_id: UUID, lesson_id: UUID, completed: bool):
    new_progress = UserLessonProgress(
        external_user_id=user_id,
        lesson_id=lesson_id,
        completed=completed
    )
    db.add(new_progress)
    await db.commit()
    await db.refresh(new_progress)
    return new_progress
