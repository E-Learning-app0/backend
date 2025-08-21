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




async def get_user_progress_by_user_id(
    db: AsyncSession,
    user_id: int
) -> UserProgress | None:
    result = await db.execute(
        select(UserProgress)
        .options(selectinload(UserProgress.module))  # Eager load module
        .where(
            UserProgress.external_user_id == user_id,
        )
    )
    return result.scalars().first()


async def get_user_progress_by_module_id(
    db: AsyncSession,
    module_id: UUID
) -> UserProgress | None:
    result = await db.execute(
        select(UserProgress)
        .options(selectinload(UserProgress.module))  # Eager load module
        .where(
            UserProgress.module_id == module_id
        )
    )
    return result.scalars().first()



async def get_user_progress_by_module_id_and_user_id(
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



async def get_all_users_progress(
    db: AsyncSession
) -> List[UserProgress]:
    """Get all progress records for a user"""
    result = await db.execute(
        select(UserProgress)
        .options(selectinload(UserProgress.module))
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
    """
    Get all modules with their unlock status based on semester progression logic
    """
    result = await db.execute(
        select(Module).options(joinedload(Module.user_progresses)).order_by(Module.order)
    )
    modules = result.unique().scalars().all()

    # Get semester completion status
    semester_completion = await get_semester_completion_status(db, user_id)
    
    response = []
    for module in modules:
        user_progress = next(
            (p for p in module.user_progresses if p.external_user_id == user_id),
            None
        )

        # Determine if module should be unlocked based on semester progression
        unlocked = await is_module_unlocked_for_user(db, user_id, module, semester_completion)
        
        # Override with explicit user progress if exists
        if user_progress:
            unlocked = user_progress.is_module_unlocked or unlocked

        response.append({
            "id": module.id,
            "title": module.title,
            "semester": module.semester,
            "is_module_unlocked": unlocked,
            "progress_percentage": user_progress.progress_percentage if user_progress else 0,
            "is_completed": user_progress.is_module_completed if user_progress else False
        })

    return response


async def get_semester_completion_status(db: AsyncSession, user_id: int) -> dict:
    """
    Calculate completion status for all semesters
    """
    semesters = ["S1", "S2", "S3", "S4"]
    completion_status = {}
    
    for semester in semesters:
        # Get all modules in semester
        result = await db.execute(
            select(Module).where(Module.semester == semester)
        )
        semester_modules = result.scalars().all()
        
        if not semester_modules:
            completion_status[semester] = False
            continue
        
        # Check how many are completed
        completed_count = 0
        for module in semester_modules:
            progress = await get_user_progress(db, user_id, module.id)
            if progress and progress.is_module_completed:
                completed_count += 1
        
        # Semester is completed if all modules are completed
        completion_status[semester] = completed_count == len(semester_modules)
    
    return completion_status


async def is_module_unlocked_for_user(db: AsyncSession, user_id: int, module: Module, semester_completion: dict) -> bool:
    """
    Determine if a module should be unlocked based on progression logic
    """
    semester = module.semester
    
    # S1 modules are always unlocked
    if semester == "S1":
        return True
    
    # S2 modules unlock when S1 is completed
    if semester == "S2":
        return semester_completion.get("S1", False)
    
    # S3 modules unlock when S2 is completed  
    if semester == "S3":
        return semester_completion.get("S2", False)
    
    # S4 modules unlock when S3 is completed
    if semester == "S4":
        return semester_completion.get("S3", False)
    
    return False


async def calculate_module_progress_percentage(db: AsyncSession, user_id: int, module_id: UUID) -> int:
    """
    Calculate progress percentage for a module based on lesson completion
    This assumes you have lesson progress tracking
    """
    # For now, return simple completion status (0% or 100%)
    # You can enhance this based on lesson progress if available
    progress = await get_user_progress(db, user_id, module_id)
    
    if not progress:
        return 0
    
    if progress.is_module_completed:
        return 100
    
    # If module is started but not completed, return progress_percentage from model
    return progress.progress_percentage or 0


async def update_module_progress_percentage(
    db: AsyncSession, 
    user_id: int, 
    module_id: UUID, 
    percentage: int
) -> UserProgress:
    """
    Update module progress percentage and handle completion logic
    """
    progress = await get_user_progress(db, user_id, module_id)
    
    if not progress:
        # Create new progress record
        progress = await create_user_progress(db, user_id, module_id, True)
    
    # Update percentage
    progress.progress_percentage = min(100, max(0, percentage))
    progress.last_accessed = datetime.utcnow()
    
    # Auto-complete if 100%
    if progress.progress_percentage == 100 and not progress.is_module_completed:
        progress.is_module_completed = True
        progress.completed_at = datetime.utcnow()
        
        # Check if this completion unlocks next semester
        await check_and_unlock_next_semester(db, user_id)
    
    await db.commit()
    await db.refresh(progress)
    return progress


async def check_and_unlock_next_semester(db: AsyncSession, user_id: int):
    """
    Check if completing a module should unlock the next semester
    """
    semester_completion = await get_semester_completion_status(db, user_id)
    
    # Define progression order
    semester_order = ["S1", "S2", "S3", "S4"]
    
    for i, semester in enumerate(semester_order[:-1]):  # Exclude last semester
        if semester_completion.get(semester, False):
            next_semester = semester_order[i + 1]
            
            # Unlock all modules in next semester
            result = await db.execute(
                select(Module).where(Module.semester == next_semester)
            )
            next_semester_modules = result.scalars().all()
            
            for module in next_semester_modules:
                progress = await get_user_progress(db, user_id, module.id)
                if not progress:
                    # Create unlocked progress for the module
                    await create_user_progress(db, user_id, module.id, is_module_unlocked=True)
                elif not progress.is_module_unlocked:
                    # Unlock existing progress
                    progress.is_module_unlocked = True
                    await db.commit()


async def get_user_dashboard_progress(db: AsyncSession, user_id: int):
    """
    Get comprehensive progress data for user dashboard
    """
    # Get all user progress
    all_progress = await get_all_user_progress(db, user_id)
    
    # Calculate semester statistics
    semester_stats = {}
    semesters = ["S1", "S2", "S3", "S4"]
    
    for semester in semesters:
        # Get modules in semester
        result = await db.execute(
            select(Module).where(Module.semester == semester)
        )
        semester_modules = result.scalars().all()
        
        completed_modules = 0
        total_modules = len(semester_modules)
        total_progress = 0
        
        for module in semester_modules:
            progress = next(
                (p for p in all_progress if p.module_id == module.id),
                None
            )
            
            if progress:
                if progress.is_module_completed:
                    completed_modules += 1
                total_progress += progress.progress_percentage
        
        avg_progress = (total_progress / total_modules) if total_modules > 0 else 0
        
        semester_stats[semester] = {
            "completed_modules": completed_modules,
            "total_modules": total_modules,
            "completion_percentage": avg_progress,
            "is_completed": completed_modules == total_modules,
            "is_accessible": await is_semester_accessible(db, user_id, semester)
        }
    
    return {
        "total_modules_completed": sum(1 for p in all_progress if p.is_module_completed),
        "total_modules": len(all_progress),
        "semester_stats": semester_stats,
        "current_semester": await get_current_semester(db, user_id)
    }


async def is_semester_accessible(db: AsyncSession, user_id: int, target_semester: str) -> bool:
    """
    Check if a semester is accessible based on progression
    """
    if target_semester == "S1":
        return True
    
    semester_completion = await get_semester_completion_status(db, user_id)
    
    semester_order = {"S1": 0, "S2": 1, "S3": 2, "S4": 3}
    target_order = semester_order.get(target_semester, 0)
    
    # Check if all previous semesters are completed
    for i in range(target_order):
        prev_semester = list(semester_order.keys())[i]
        if not semester_completion.get(prev_semester, False):
            return False
    
    return True


async def get_current_semester(db: AsyncSession, user_id: int) -> str:
    """
    Determine the current semester the user should be working on
    """
    semester_completion = await get_semester_completion_status(db, user_id)
    
    # Find the first incomplete semester
    semesters = ["S1", "S2", "S3", "S4"]
    for semester in semesters:
        if not semester_completion.get(semester, False):
            return semester
    
    # All semesters completed, return last one
    return "S4"


async def unlock_semester_modules(db: AsyncSession, user_id: int, semester: str):
    """
    Unlock all modules in a specific semester for a user
    """
    result = await db.execute(
        select(Module).where(Module.semester == semester)
    )
    modules = result.scalars().all()
    
    for module in modules:
        progress = await get_user_progress(db, user_id, module.id)
        if not progress:
            await create_user_progress(db, user_id, module.id, is_module_unlocked=True)
        elif not progress.is_module_unlocked:
            progress.is_module_unlocked = True
            await db.commit()
