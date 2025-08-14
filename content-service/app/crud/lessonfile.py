from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.models.lesson_file import LessonFile
from app.schemas.lessonfile import LessonFileCreate, LessonFileUpdate

async def get_lessonfile(db: AsyncSession, lessonfile_id: UUID) -> LessonFile | None:
    result = await db.execute(select(LessonFile).where(LessonFile.id == lessonfile_id))
    return result.scalar_one_or_none()

async def get_lessonfiles_by_lesson(db: AsyncSession, lesson_id: UUID) -> list[LessonFile]:
    result = await db.execute(select(LessonFile).where(LessonFile.lesson_id == lesson_id))
    return result.scalars().all()

async def create_lessonfile(db: AsyncSession, lessonfile_in: LessonFileCreate) -> LessonFile:
    new_file = LessonFile(**lessonfile_in.dict())
    db.add(new_file)
    await db.commit()
    await db.refresh(new_file)
    return new_file

async def update_lessonfile(db: AsyncSession, lessonfile_id: UUID, update_data: LessonFileUpdate) -> LessonFile | None:
    lessonfile = await get_lessonfile(db, lessonfile_id)
    if not lessonfile:
        return None
    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(lessonfile, key, value)
    await db.commit()
    await db.refresh(lessonfile)
    return lessonfile

async def delete_lessonfile(db: AsyncSession, lessonfile_id: UUID) -> bool:
    lessonfile = await get_lessonfile(db, lessonfile_id)
    if not lessonfile:
        return False
    await db.delete(lessonfile)
    await db.commit()
    return True
