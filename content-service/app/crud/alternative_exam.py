# app/crud/exam.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from sqlalchemy import update
from app.models.user_exams import UserExam
from uuid import UUID
from sqlalchemy import and_, func
import os
from app.models.alternative_exam import AlternativeExam
import uuid, json
from datetime import datetime
from uuid import UUID


async def get_alternative_exam(db: AsyncSession, module_id: UUID):
    result = await db.execute(
        select(AlternativeExam).where(AlternativeExam.module_id == module_id)
    )
    return result.scalars().first()


