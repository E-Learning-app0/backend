# app/services/progress_utils.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.module import Module
from app.models.user_progress import UserProgress
from datetime import datetime

semester_order = ["S1", "S2", "S3", "S4"]

async def try_unlock_next_semester_async(db: AsyncSession, user_id: int, current_semester: str):
    if current_semester not in semester_order:
        return {"unlocked": False, "message": "Unknown semester format"}

    current_index = semester_order.index(current_semester)
    if current_index == len(semester_order) - 1:
        return {"unlocked": False, "message": "Last semester reached"}

    # Get current semester modules
    result = await db.execute(select(Module).where(Module.semester == current_semester))
    current_modules = result.scalars().all()

    result = await db.execute(
        select(UserProgress).where(
            UserProgress.external_user_id == user_id,
            UserProgress.is_module_completed == True,
            UserProgress.module_id.in_([m.id for m in current_modules])
        )
    )
    completed = result.scalars().all()

    if len(completed) < len(current_modules):
        return {"unlocked": False, "message": "Current semester not fully completed"}

    # Unlock next semester modules
    next_semester = semester_order[current_index + 1]
    result = await db.execute(select(Module).where(Module.semester == next_semester))
    next_modules = result.scalars().all()

    for mod in next_modules:
        result = await db.execute(
            select(UserProgress).where(
                UserProgress.external_user_id == user_id,
                UserProgress.module_id == mod.id
            )
        )
        existing = result.scalar_one_or_none()

        if not existing:
            new_progress = UserProgress(
                external_user_id=user_id,
                module_id=mod.id,
                is_module_unlocked=True,
                last_accessed=datetime.utcnow()
            )
            db.add(new_progress)

    await db.commit()
    return {"unlocked": True, "message": f"{next_semester} modules unlocked"}
