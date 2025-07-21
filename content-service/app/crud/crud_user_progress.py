from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from datetime import datetime
from typing import List
from sqlalchemy.orm import joinedload


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


from sqlalchemy import asc
"""

async def get_modules_with_unlock_status(db: AsyncSession, user_id: int):
    # Récupérer tous les modules
    result = await db.execute(
        select(Module).options(joinedload(Module.user_progresses))
        .order_by(asc(Module.order))
    )
    modules = result.unique().scalars().all()

    # Créer une réponse avec les états de déblocage
    response = []
    for module in modules:
        user_progress = next(
            (progress for progress in module.user_progresses if progress.external_user_id == user_id),
            None
        )
        response.append({
            "id": module.id,
            "title": module.title,
            "semester": module.semester,
            "is_module_unlocked": user_progress.is_module_unlocked if user_progress else False
        })

    return response

"""


async def get_highest_unlocked_semester_for_user(db: AsyncSession, user_id: int) -> str:
    # 1. Get all semesters ordered ascending, e.g., ["S1", "S2", "S3", ...]
    semesters_result = await db.execute(
        select(Module.semester).distinct().order_by(Module.semester)
    )
    semesters = [row[0] for row in semesters_result.all()]

    highest_unlocked = "S1"  # Default to first semester

    for semester in semesters:
        # 2. Get all modules in the semester
        modules_result = await db.execute(
            select(Module.id).where(Module.semester == semester)
        )
        module_ids = [row[0] for row in modules_result.all()]

        # 3. Check if user completed all these modules
        # Assuming you have UserProgress or ExamResult table to check completion
        # For example, count modules completed by user in this semester
        completed_result = await db.execute(
            select(func.count())
            .select_from(UserProgress)
            .where(
                UserProgress.external_user_id == user_id,
                UserProgress.module_id.in_(module_ids),
                UserProgress.is_module_completed == True  # or whatever field indicates completion
            )
        )
        completed_count = completed_result.scalar()

        # 4. Check if all modules in semester completed
        if completed_count == len(module_ids):
            # User completed this semester fully, unlock next one
            highest_unlocked = semester
        else:
            # Found a semester not fully completed, stop checking further semesters
            break

    return highest_unlocked







async def get_modules_with_unlock_status(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(Module).options(joinedload(Module.user_progresses)).order_by(Module.order)
    )
    modules = result.unique().scalars().all()

    # Determine the highest semester unlocked for the user
    # For example, check which semesters are fully completed
    # (You'll need additional queries for exam results, progress, etc.)
    highest_unlocked_semester = await get_highest_unlocked_semester_for_user(db, user_id)

    response = []
    for module in modules:
        user_progress = next(
            (p for p in module.user_progresses if p.external_user_id == user_id),
            None
        )

        # Unlock S1 by default, or unlock if semester <= highest unlocked
        if module.semester == "S1":
            unlocked = True
        else:
            # Unlock if current module's semester is <= highest unlocked semester
            unlocked = module.semester <= highest_unlocked_semester

        # You can override unlocked flag if user_progress shows unlocked explicitly
        if user_progress:
            unlocked = user_progress.is_module_unlocked

        response.append({
            "id": module.id,
            "title": module.title,
            "semester": module.semester,
            "is_module_unlocked": unlocked
        })

    return response
