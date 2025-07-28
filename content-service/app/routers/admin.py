# app/routers/admin.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.db.session import get_db
from app.dependencies.roles import require_any_role
from app.models.lesson import Lesson
from app.models.module import Module

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/stats/modules")
async def get_modules_stats(
    db: AsyncSession = Depends(get_db),
    user = Depends(require_any_role("admin"))
):
    """Get total number of modules"""
    try:
        stmt = select(func.count(Module.id))
        result = await db.execute(stmt)
        count = result.scalar()
        return {"count": count, "type": "modules"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting modules stats: {str(e)}")

@router.get("/stats/lessons")
async def get_lessons_stats(
    db: AsyncSession = Depends(get_db),
    user = Depends(require_any_role("admin"))
):
    """Get total number of lessons"""
    try:
        stmt = select(func.count(Lesson.id))
        result = await db.execute(stmt)
        count = result.scalar()
        return {"count": count, "type": "lessons"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting lessons stats: {str(e)}")

@router.get("/stats/videos")
async def get_videos_stats(
    db: AsyncSession = Depends(get_db),
    user = Depends(require_any_role("admin"))
):
    """Get total number of lessons with videos"""
    try:
        stmt = select(func.count(Lesson.id)).where(
            Lesson.video.isnot(None),
            Lesson.video != ''
        )
        result = await db.execute(stmt)
        count = result.scalar()
        return {"count": count, "type": "videos"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting videos stats: {str(e)}")

@router.get("/stats/quizzes")
async def get_quizzes_stats(
    db: AsyncSession = Depends(get_db),
    user = Depends(require_any_role("admin"))
):
    """Get total number of lessons with quizzes"""
    try:
        stmt = select(func.count(Lesson.id)).where(
            Lesson.quiz_id.isnot(None),
            Lesson.quiz_id != ''
        )
        result = await db.execute(stmt)
        count = result.scalar()
        return {"count": count, "type": "quizzes"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting quizzes stats: {str(e)}")

@router.get("/stats/pdfs")
async def get_pdfs_stats(
    db: AsyncSession = Depends(get_db),
    user = Depends(require_any_role("admin"))
):
    """Get total number of lessons with PDFs"""
    try:
        stmt = select(func.count(Lesson.id)).where(
            Lesson.pdf.isnot(None),
            Lesson.pdf != ''
        )
        result = await db.execute(stmt)
        count = result.scalar()
        return {"count": count, "type": "pdfs"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting PDFs stats: {str(e)}")

@router.get("/stats/summary")
async def get_admin_summary(
    db: AsyncSession = Depends(get_db),
    user = Depends(require_any_role("admin"))
):
    """Get comprehensive admin statistics"""
    try:
        # Get all stats in parallel
        modules_stmt = select(func.count(Module.id))
        lessons_stmt = select(func.count(Lesson.id))
        videos_stmt = select(func.count(Lesson.id)).where(
            Lesson.video.isnot(None), Lesson.video != ''
        )
        quizzes_stmt = select(func.count(Lesson.id)).where(
            Lesson.quiz_id.isnot(None), Lesson.quiz_id != ''
        )
        pdfs_stmt = select(func.count(Lesson.id)).where(
            Lesson.pdf.isnot(None), Lesson.pdf != ''
        )
        
        # Execute all queries
        modules_result = await db.execute(modules_stmt)
        lessons_result = await db.execute(lessons_stmt)
        videos_result = await db.execute(videos_stmt)
        quizzes_result = await db.execute(quizzes_stmt)
        pdfs_result = await db.execute(pdfs_stmt)
        
        return {
            "modules": modules_result.scalar(),
            "lessons": lessons_result.scalar(),
            "videos": videos_result.scalar(),
            "quizzes": quizzes_result.scalar(),
            "pdfs": pdfs_result.scalar(),
            "timestamp": "2025-01-27T00:00:00Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting admin summary: {str(e)}")

@router.get("/lessons/without-videos")
async def get_lessons_without_videos(
    db: AsyncSession = Depends(get_db),
    user = Depends(require_any_role("admin", "teacher"))
):
    """Get lessons that don't have videos"""
    try:
        stmt = select(Lesson).where(
            (Lesson.video.is_(None)) | (Lesson.video == '')
        )
        result = await db.execute(stmt)
        lessons = result.scalars().all()
        
        return {
            "count": len(lessons),
            "lessons": [
                {
                    "id": str(lesson.id),
                    "title": lesson.title,
                    "moduleid": str(lesson.moduleid)
                }
                for lesson in lessons
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting lessons without videos: {str(e)}")

@router.get("/lessons/without-quizzes")
async def get_lessons_without_quizzes(
    db: AsyncSession = Depends(get_db),
    user = Depends(require_any_role("admin", "teacher"))
):
    """Get lessons that don't have quizzes"""
    try:
        stmt = select(Lesson).where(
            (Lesson.quiz_id.is_(None)) | (Lesson.quiz_id == '')
        )
        result = await db.execute(stmt)
        lessons = result.scalars().all()
        
        return {
            "count": len(lessons),
            "lessons": [
                {
                    "id": str(lesson.id),
                    "title": lesson.title,
                    "moduleid": str(lesson.moduleid),
                    "has_pdf": lesson.pdf is not None and lesson.pdf != ''
                }
                for lesson in lessons
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting lessons without quizzes: {str(e)}")
