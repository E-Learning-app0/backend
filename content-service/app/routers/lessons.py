from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from app.db.session import get_db
from app.schemas.lesson import LessonRead, LessonCreate, LessonUpdate,LessonWithProgress
from app.crud.lesson import get_lesson, create_lesson, update_lesson, delete_lesson,get_lessons_by_module,get_lesson_with_progress, reorder_lessons_for_module, update_lesson_order
from app.dependencies.roles import require_any_role

router = APIRouter(prefix="/lessons", tags=["Lessons"])

@router.get("/{lesson_id}", response_model=LessonRead)
async def read_lesson(
    lesson_id: UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_any_role("admin", "teacher", "student"))  # All can read
):
    lesson = await get_lesson(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson



@router.get("/module/{module_id}", response_model=List[LessonRead])
async def read_lessons_by_module(module_id: UUID, db: AsyncSession = Depends(get_db),
                                 user=Depends(require_any_role("admin", "teacher", "student")) ):
    
    lessons = await get_lessons_by_module(db, module_id)
    return lessons

@router.post("/", response_model=LessonRead, status_code=status.HTTP_201_CREATED)
async def create_new_lesson(
    lesson_in: LessonCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_any_role("admin", "teacher"))  # Only teachers or admins can create
):
    return await create_lesson(db, lesson_in)


@router.put("/{lesson_id}", response_model=LessonRead)
async def update_existing_lesson(lesson_id: UUID, lesson_in: LessonUpdate, db: AsyncSession = Depends(get_db),
                                 user=Depends(require_any_role("admin", "teacher"))):
    existing = await get_lesson(db, lesson_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Lesson not found")
    updated = await update_lesson(db, lesson_id, lesson_in)
    if not updated:
        raise HTTPException(status_code=400, detail="Failed to update lesson")
    return updated[0]  # car returning(Lesson) renvoie un tuple

@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_lesson(lesson_id: UUID, db: AsyncSession = Depends(get_db),
                                 user=Depends(require_any_role("admin"))):
    existing = await get_lesson(db, lesson_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Lesson not found")
    await delete_lesson(db, lesson_id)
    return


@router.get("/with-progress/{lesson_id}", response_model=LessonWithProgress)
async def get_lesson_progress(
    lesson_id: UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_any_role("admin", "teacher", "student"))
):
    try:
        return await get_lesson_with_progress(db, lesson_id, user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/reorder-module/{module_id}")
async def fix_lesson_order_for_module(
    module_id: UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_any_role("admin", "teacher"))
):
    """Fix orderindex for all lessons in a module by reassigning sequential numbers"""
    try:
        count = await reorder_lessons_for_module(db, module_id)
        return {"message": f"Reordered {count} lessons in module", "module_id": module_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to reorder lessons: {str(e)}")


@router.put("/{lesson_id}/order/{new_order}")
async def change_lesson_order(
    lesson_id: UUID,
    new_order: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_any_role("admin", "teacher"))
):
    """Change a lesson's order position and adjust other lessons accordingly"""
    try:
        updated_lesson = await update_lesson_order(db, lesson_id, new_order)
        if not updated_lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        return {"message": f"Lesson moved to position {new_order}", "lesson_id": lesson_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update lesson order: {str(e)}")
