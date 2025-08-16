from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.exam import get_exam_by_id, create_exam, update_exam

from app.db.session import get_db
router = APIRouter(prefix="/exams", tags=["Exams"])

@router.post("/")
async def create_exam_endpoint(exam: dict, db: AsyncSession = Depends(get_db)):
    existing = await get_exam_by_id(db, exam["id"])
    
    if existing:
        updated = await update_exam(db, existing, exam)
        return {"message": "Exam updated", "id": updated.id}
    
    new_exam = await create_exam(db, exam)
    return {"message": "Exam created", "id": new_exam.id}
