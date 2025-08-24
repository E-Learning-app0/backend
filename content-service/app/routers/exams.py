# app/api/endpoints/exams.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from app.api.deps import get_current_user
from app.crud.exam import (
    get_exam_by_id,
    get_exam_by_user_and_module, 
    create_user_exam_from_redis, 
    update_user_exam,
    get_user_exams,
    get_module_exams_for_user,
    get_user_passed_exams_count,
    get_exam_from_redis,
    get_user_module_attempts
)
from app.db.session import get_db
from app.schemas.exam import ExamCreate, ExamUpdate, ExamResponse,ExamCreatedResponse
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("agent-service")  # custom logger
router = APIRouter(prefix="/exams", tags=["Exams"])




@router.post("/create", response_model=ExamCreatedResponse)
async def create_exam_from_redis(exam_req: ExamCreate, db: AsyncSession = Depends(get_db),
current_user: dict = Depends(get_current_user)):
    """
    Create or update exam for a specific user and module
    """
    
    logger.info("Start Post api Create stuff...")
    # Check if exam already exists for this user and module
    passed_exams_count  = await get_user_passed_exams_count(
        db, current_user.id, exam_req.module_id
    )

    logger.info("-----Passed exams count: %d", passed_exams_count)
    if passed_exams_count > 0:
        raise HTTPException(
            status_code=409,
            detail="Module already passed. Cannot retake."
        )
    
    logger.info("-----Start redis")
    # Check if exam exists in Redis
    redis_exam = await get_exam_from_redis(current_user.id, exam_req.module_id)
    if not redis_exam:
        raise HTTPException(
            status_code=404, 
            detail="Exam not found in Redis. Generate exam first."
        )
    
    logger.info("-----Start get_user_module_attempts")
    previous_attempts = await get_user_module_attempts(db, current_user.id, exam_req.module_id)
    is_retake = previous_attempts > 0
    # Create new exam
    try:
        new_exam = await create_user_exam_from_redis(
            db,
            current_user.id,
            exam_req.module_id,
            is_retake=is_retake,
            attempt_number=previous_attempts + 1
        )
        
        return {
            "message": "Exam created successfully",
            "exam_id": new_exam.id,
            "status": "created",
            "is_retake": is_retake,
            "attempt_number": new_exam.attempt_number
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error creating exam: {str(e)}"
        )




@router.get("/user/{user_id}", response_model=List[ExamResponse])
async def get_user_all_exams(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get all exams for a specific user
    """
    exams = await get_user_exams(db, user_id)
    return exams




@router.get("/user/{user_id}/module/{module_id}", response_model=List[ExamResponse])
async def get_user_module_exams(
    user_id: int, 
    module_id: UUID, 
    db: AsyncSession = Depends(get_db)
):
    """
    Get all exams for a specific user and module
    """
    exams = await get_module_exams_for_user(db, user_id, module_id)
    return exams

@router.get("/{exam_id}", response_model=ExamResponse)
async def get_exam_by_id_endpoint(exam_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get specific exam by ID
    """
    exam = await get_exam_by_id(db, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam