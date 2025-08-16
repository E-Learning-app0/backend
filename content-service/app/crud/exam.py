from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from app.models.exam import Exam
from uuid import UUID

async def get_exam_by_id(db: AsyncSession, exam_id: UUID):
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    return result.scalars().first()

async def create_exam(db: AsyncSession, exam_data: dict):
    new_exam = Exam(
        id=exam_data["id"],
        title=exam_data["title"],
        description=exam_data.get("description"),
        content=exam_data["content"],
        module_id=exam_data.get("module_id")
    )
    db.add(new_exam)
    await db.commit()
    await db.refresh(new_exam)
    return new_exam

async def update_exam(db: AsyncSession, existing_exam: Exam, exam_data: dict):
    existing_exam.title = exam_data["title"]
    existing_exam.content = exam_data["content"]
    existing_exam.description = exam_data.get("description")
    await db.commit()
    await db.refresh(existing_exam)
    return existing_exam
