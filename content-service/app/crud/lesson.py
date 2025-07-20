# app/crud/lesson.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from app.models.lesson import Lesson
from app.models.user_lesson_progress import UserLessonProgress
from app.schemas.lesson import LessonCreate, LessonUpdate,LessonWithProgress
from uuid import UUID

async def get_lesson(db: AsyncSession, lesson_id: UUID):
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    return result.scalars().first()

async def create_lesson(db: AsyncSession, lesson_create: LessonCreate):
    new_lesson = Lesson(**lesson_create.dict())
    db.add(new_lesson)
    await db.commit()
    await db.refresh(new_lesson)
    return new_lesson

async def update_lesson(db: AsyncSession, lesson_id: UUID, lesson_update: LessonUpdate):
    stmt = update(Lesson).where(Lesson.id == lesson_id).values(**lesson_update.dict()).returning(Lesson)
    result = await db.execute(stmt)
    await db.commit()
    updated = result.fetchone()
    return updated

async def delete_lesson(db: AsyncSession, lesson_id: UUID):
    stmt = delete(Lesson).where(Lesson.id == lesson_id)
    await db.execute(stmt)
    await db.commit()


from typing import List

async def get_lessons_by_module(db: AsyncSession, module_id: UUID) -> List[Lesson]:
    result = await db.execute(
        select(Lesson).where(Lesson.moduleid == module_id).order_by(Lesson.orderindex)
    )
    return result.scalars().all()




async def get_lesson_with_progress(
    db: AsyncSession, lesson_id: UUID, user_id: UUID
) -> LessonWithProgress:
    stmt = (
        select(Lesson.id, Lesson.title, UserLessonProgress.completed)
        .join(UserLessonProgress, Lesson.id == UserLessonProgress.lesson_id)
        .where(Lesson.id == lesson_id, UserLessonProgress.user_id == user_id)
    )
    result = await db.execute(stmt)
    row = result.fetchone()

    if not row:
        raise ValueError("Lesson not found or no progress for user")

    return LessonWithProgress(id=row.id, title=row.title, completed=row.completed)