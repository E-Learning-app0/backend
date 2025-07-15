from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.models.teacher import Teacher
from app.schemas.teacher import TeacherCreate, TeacherUpdate

async def get_teacher(db: AsyncSession, teacher_id: UUID) -> Teacher | None:
    result = await db.execute(select(Teacher).where(Teacher.id == teacher_id))
    return result.scalar_one_or_none()

async def get_teachers(db: AsyncSession) -> list[Teacher]:
    result = await db.execute(select(Teacher))
    return result.scalars().all()

async def create_teacher(db: AsyncSession, teacher_in: TeacherCreate) -> Teacher:
    new_teacher = Teacher(**teacher_in.dict())
    db.add(new_teacher)
    await db.commit()
    await db.refresh(new_teacher)
    return new_teacher

async def update_teacher(db: AsyncSession, teacher_id: UUID, teacher_in: TeacherUpdate) -> Teacher | None:
    teacher = await get_teacher(db, teacher_id)
    if not teacher:
        return None
    for key, value in teacher_in.dict(exclude_unset=True).items():
        setattr(teacher, key, value)
    await db.commit()
    await db.refresh(teacher)
    return teacher

async def delete_teacher(db: AsyncSession, teacher_id: UUID) -> bool:
    teacher = await get_teacher(db, teacher_id)
    if not teacher:
        return False
    await db.delete(teacher)
    await db.commit()
    return True
