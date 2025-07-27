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
    lesson_data = lesson_create.dict()
    
    # Auto-assign orderindex if not provided
    if lesson_data.get('orderindex') is None:
        # Get the highest orderindex for this module
        stmt = select(Lesson.orderindex).where(
            Lesson.moduleid == lesson_data['moduleid'],
            Lesson.orderindex.isnot(None)
        ).order_by(Lesson.orderindex.desc())
        result = await db.execute(stmt)
        max_order = result.scalars().first()
        lesson_data['orderindex'] = (max_order + 1) if max_order else 1
    
    new_lesson = Lesson(**lesson_data)
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

async def update_lesson_quiz_id(db: AsyncSession, lesson_id: UUID, quiz_id: str):
    """Update only the quiz_id field of a lesson"""
    stmt = update(Lesson).where(Lesson.id == lesson_id).values(quiz_id=quiz_id).returning(Lesson)
    result = await db.execute(stmt)
    await db.commit()
    updated = result.fetchone()
    return updated

async def get_lessons_without_quiz(db: AsyncSession):
    """Get all lessons that have PDF content but no quiz_id"""
    stmt = select(Lesson).where(
        Lesson.pdf.isnot(None),
        Lesson.pdf != '',
        Lesson.quiz_id.is_(None)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

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


async def reorder_lessons_for_module(db: AsyncSession, module_id: UUID):
    """Fix orderindex for all lessons in a module by reassigning 1, 2, 3, etc."""
    # Get all lessons for this module ordered by current orderindex, then by creation date
    stmt = select(Lesson).where(Lesson.moduleid == module_id).order_by(
        Lesson.orderindex.asc().nulls_last(), 
        Lesson.createdat.asc()
    )
    result = await db.execute(stmt)
    lessons = result.scalars().all()
    
    # Update each lesson with new sequential orderindex
    for index, lesson in enumerate(lessons, 1):
        await db.execute(
            update(Lesson).where(Lesson.id == lesson.id).values(orderindex=index)
        )
    
    await db.commit()
    return len(lessons)


async def update_lesson_order(db: AsyncSession, lesson_id: UUID, new_order: int):
    """Update a specific lesson's order and adjust other lessons accordingly"""
    # Get the lesson and its module
    lesson_stmt = select(Lesson).where(Lesson.id == lesson_id)
    lesson_result = await db.execute(lesson_stmt)
    lesson = lesson_result.scalars().first()
    
    if not lesson:
        return None
    
    # Get current max order in the module
    max_stmt = select(Lesson.orderindex).where(
        Lesson.moduleid == lesson.moduleid,
        Lesson.orderindex.isnot(None)
    ).order_by(Lesson.orderindex.desc())
    max_result = await db.execute(max_stmt)
    max_order = max_result.scalars().first() or 0
    
    # Ensure new_order is within bounds
    new_order = max(1, min(new_order, max_order + 1))
    
    old_order = lesson.orderindex or max_order + 1
    
    if old_order == new_order:
        return lesson  # No change needed
    
    # Shift other lessons
    if new_order < old_order:
        # Moving up: shift lessons down
        await db.execute(
            update(Lesson).where(
                Lesson.moduleid == lesson.moduleid,
                Lesson.orderindex >= new_order,
                Lesson.orderindex < old_order,
                Lesson.id != lesson_id
            ).values(orderindex=Lesson.orderindex + 1)
        )
    else:
        # Moving down: shift lessons up
        await db.execute(
            update(Lesson).where(
                Lesson.moduleid == lesson.moduleid,
                Lesson.orderindex > old_order,
                Lesson.orderindex <= new_order,
                Lesson.id != lesson_id
            ).values(orderindex=Lesson.orderindex - 1)
        )
    
    # Update the target lesson
    await db.execute(
        update(Lesson).where(Lesson.id == lesson_id).values(orderindex=new_order)
    )
    
    await db.commit()
    await db.refresh(lesson)
    return lesson




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