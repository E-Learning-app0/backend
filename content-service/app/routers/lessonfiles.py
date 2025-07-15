from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.schemas.lessonfile import LessonFileRead, LessonFileCreate, LessonFileUpdate
from app.crud.lessonfile import (
    get_lessonfile, get_lessonfiles_by_lesson,
    create_lessonfile, update_lessonfile, delete_lessonfile
)

router = APIRouter(prefix="/lessonfiles", tags=["LessonFiles"])

@router.get("/{lessonfile_id}", response_model=LessonFileRead)
async def read_lessonfile(lessonfile_id: UUID, db: AsyncSession = Depends(get_db)):
    lessonfile = await get_lessonfile(db, lessonfile_id)
    if not lessonfile:
        raise HTTPException(status_code=404, detail="LessonFile not found")
    return lessonfile

@router.get("/lesson/{lesson_id}", response_model=List[LessonFileRead])
async def read_files_by_lesson(lesson_id: UUID, db: AsyncSession = Depends(get_db)):
    files = await get_lessonfiles_by_lesson(db, lesson_id)
    return files

@router.post("/", response_model=LessonFileRead, status_code=status.HTTP_201_CREATED)
async def create_new_lessonfile(lessonfile_in: LessonFileCreate, db: AsyncSession = Depends(get_db)):
    new_file = await create_lessonfile(db, lessonfile_in)
    return new_file

@router.put("/{lessonfile_id}", response_model=LessonFileRead)
async def update_existing_lessonfile(lessonfile_id: UUID, lessonfile_in: LessonFileUpdate, db: AsyncSession = Depends(get_db)):
    updated_file = await update_lessonfile(db, lessonfile_id, lessonfile_in)
    if not updated_file:
        raise HTTPException(status_code=404, detail="LessonFile not found")
    return updated_file

@router.delete("/{lessonfile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_lessonfile(lessonfile_id: UUID, db: AsyncSession = Depends(get_db)):
    success = await delete_lessonfile(db, lessonfile_id)
    if not success:
        raise HTTPException(status_code=404, detail="LessonFile not found")
    return
