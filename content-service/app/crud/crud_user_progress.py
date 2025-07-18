from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from datetime import datetime
from typing import List

from app.models.user_progress import UserProgress
from app.models.module import Module


async def get_user_progress(
    db: AsyncSession,
    user_id: int,
    module_id: UUID
) -> UserProgress | None:
    """Get a single user progress record"""
    result = await db.execute(
        select(UserProgress)
        .where(
            UserProgress.external_user_id == user_id,
            UserProgress.module_id == module_id
        )
    )
    return result.scalars().first()


async def get_user_progress_with_module(
    db: AsyncSession,
    user_id: int,
    module_id: UUID
) -> UserProgress | None:
    result = await db.execute(
        select(UserProgress)
        .options(selectinload(UserProgress.module))  # Eager load module
        .where(
            UserProgress.external_user_id == user_id,
            UserProgress.module_id == module_id
        )
    )
    return result.scalars().first()


async def get_user_progress_by_semester(
    db: AsyncSession,
    user_id: int,
    semester: str
) -> List[UserProgress]:
    """Get all user progress records for a specific semester"""
    result = await db.execute(
        select(UserProgress)
        .options(selectinload(UserProgress.module))
        .join(Module)
        .where(
            UserProgress.external_user_id == user_id,
            Module.semester == semester
        )
    )
    return result.scalars().all()


async def get_all_user_progress(
    db: AsyncSession,
    user_id: int
) -> List[UserProgress]:
    """Get all progress records for a user"""
    result = await db.execute(
        select(UserProgress)
        .options(selectinload(UserProgress.module))
        .where(UserProgress.external_user_id == user_id)
    )
    return result.scalars().all()


async def create_user_progress(
    db: AsyncSession,
    user_id: int,
    module_id: UUID,
    is_module_unlocked: bool = True
) -> UserProgress:
    """Create a new user progress record"""
    progress = UserProgress(
        external_user_id=user_id,
        module_id=module_id,
        is_module_unlocked=is_module_unlocked,
        last_accessed=datetime.utcnow()
    )
    db.add(progress)
    await db.commit()
    await db.refresh(progress)
    return progress


async def unlock_module(
    db: AsyncSession,
    user_id: int,
    module_id: UUID
) -> UserProgress:
    """Unlock module for user"""
    progress = await get_user_progress(db, user_id, module_id)
    if not progress:
        progress = await create_user_progress(db, user_id, module_id, True)
    else:
        progress.is_module_unlocked = True
        progress.last_accessed = datetime.utcnow()
        await db.commit()
        await db.refresh(progress)
    return progress


async def mark_module_completed(
    db: AsyncSession,
    user_id: int,
    module_id: UUID
) -> UserProgress:
    """Mark module as completed"""
    progress = await get_user_progress(db, user_id, module_id)
    if not progress:
        progress = await create_user_progress(db, user_id, module_id)
        progress.is_module_completed = True
    else:
        progress.is_module_completed = True
        progress.completed_at = datetime.utcnow()
    
    progress.last_accessed = datetime.utcnow()
    await db.commit()
    await db.refresh(progress)
    return progress


async def update_user_progress(
    db: AsyncSession,
    user_id: int,
    module_id: UUID,
    update_data: dict
) -> UserProgress | None:
    """Update user progress with partial data"""
    progress = await get_user_progress(db, user_id, module_id)
    if not progress:
        return None
    
    for field, value in update_data.items():
        if hasattr(progress, field):
            setattr(progress, field, value)
    
    progress.last_accessed = datetime.utcnow()
    await db.commit()
    await db.refresh(progress)
    return progress


async def delete_user_progress(
    db: AsyncSession,
    user_id: int,
    module_id: UUID
) -> bool:
    """Delete a user progress record"""
    progress = await get_user_progress(db, user_id, module_id)
    if not progress:
        return False
    
    await db.delete(progress)
    await db.commit()
    return True


async def get_completed_modules_count(
    db: AsyncSession,
    user_id: int
) -> int:
    """Get count of completed modules for a user"""
    result = await db.execute(
        select(func.count())
        .select_from(UserProgress)
        .where(
            UserProgress.external_user_id == user_id,
            UserProgress.is_module_completed == True
        )
    )
    return result.scalar() or 0


async def get_unlocked_modules_count(
    db: AsyncSession,
    user_id: int
) -> int:
    """Get count of unlocked modules for a user"""
    result = await db.execute(
        select(func.count())
        .select_from(UserProgress)
        .where(
            UserProgress.external_user_id == user_id,
            UserProgress.is_module_unlocked == True
        )
    )
    return result.scalar() or 0