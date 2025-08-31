from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.db.session import get_db
from app.crud.alternative_exam import get_alternative_exam

router = APIRouter(prefix="/alternative-exam", tags=["AlternativeExam"])

@router.get("/{module_id}")
async def read_alternative_exam(module_id: UUID, version: int = 1, db: AsyncSession = Depends(get_db)):
    alternative_exam = await get_alternative_exam(db, module_id,version)
    if alternative_exam:
        return {
            "version": alternative_exam.version,
            "content": alternative_exam.content
            }
    raise HTTPException(status_code=404, detail="Alternative exam not found")

    


