from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.schemas.teacher import TeacherRead, TeacherCreate, TeacherUpdate
from app.crud.teacher import (
    get_teacher, get_teachers,
    create_teacher, update_teacher, delete_teacher
)
from app.dependencies.roles import require_any_role

router = APIRouter(prefix="/teachers", tags=["Teachers"])

@router.get("/", response_model=List[TeacherRead])
async def read_teachers(db: AsyncSession = Depends(get_db)):
    teachers = await get_teachers(db)
    return teachers

@router.get("/{teacher_id}", response_model=TeacherRead)
async def read_teacher(teacher_id: UUID, db: AsyncSession = Depends(get_db)):
    teacher = await get_teacher(db, teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return teacher

@router.post("/", response_model=TeacherRead, status_code=status.HTTP_201_CREATED)
async def create_new_teacher(teacher_in: TeacherCreate, db: AsyncSession = Depends(get_db)):
    new_teacher = await create_teacher(db, teacher_in)
    return new_teacher

@router.put("/{teacher_id}", response_model=TeacherRead)
async def update_existing_teacher(teacher_id: UUID, teacher_in: TeacherUpdate, db: AsyncSession = Depends(get_db)):
    updated_teacher = await update_teacher(db, teacher_id, teacher_in)
    if not updated_teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return updated_teacher

@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_teacher(teacher_id: UUID, db: AsyncSession = Depends(get_db)):
    success = await delete_teacher(db, teacher_id)
    if not success:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return
