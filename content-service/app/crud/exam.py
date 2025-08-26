# app/crud/exam.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from sqlalchemy import update
from app.models.user_exams import UserExam
from uuid import UUID
from sqlalchemy import and_, func
import os
import redis
import uuid, json
from datetime import datetime
from uuid import UUID

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

if REDIS_PASSWORD:
    r = redis.Redis(
        host=REDIS_HOST, 
        port=REDIS_PORT, 
        db=0,
        password=REDIS_PASSWORD,
        ssl=True,
        ssl_check_hostname=False,
        ssl_cert_reqs=None
    )
else:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

async def get_exam_by_user_and_module(db: AsyncSession, user_id: int, module_id: UUID):
    result = await db.execute(
        select(UserExam).where(
            and_(
                UserExam.external_user_id == user_id,
                UserExam.module_id == module_id
            )
        )
    )
    return result.scalars().first()

async def get_exam_by_id(db: AsyncSession, exam_id: UUID):
    result = await db.execute(select(UserExam).where(UserExam.id == exam_id))
    return result.scalars().first()


import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("agent-service")  # custom logger

async def get_exam_from_redis(user_id: int, module_id: UUID):
    """Get exam data from Redis using user_id + module_id index"""
    logger.info("-----Start get stuff from redis")

    # First get exam_id from user+module index
    exam_id_key = f"user:{user_id}:module:{module_id}:exam"
    logger.info("Looking for exam_id with key: %s", exam_id_key)

    exam_id = r.get(exam_id_key)
    if not exam_id:
        logger.info("No exam_id found for key %s", exam_id_key)
        return None

    exam_id = exam_id.decode("utf-8")  # <-- decode bytes to string
    logger.info("-----Got exam id from redis: %s", exam_id)

    # Then get full exam data
    exam_data = r.get(f"exam:{exam_id}")
    if not exam_data:
        logger.info("No exam data found for key exam:%s", exam_id)
        return None

    exam_data = exam_data.decode("utf-8")  # <-- decode bytes to string
    logger.info("-----Got exam data from redis: %s", exam_data)

    return json.loads(exam_data)


async def get_user_exams_from_redis(user_id: int):
    """Get all exam IDs for a user"""
    exam_ids = r.smembers(f"user:{user_id}:exams")
    exams = []
    
    for exam_id in exam_ids:
        exam_data = r.get(f"exam:{exam_id}")
        if exam_data:
            exams.append(json.loads(exam_data))
    
    return exams

async def get_module_exams_from_redis(module_id: UUID):
    """Get all exam IDs for a module"""
    exam_ids = r.smembers(f"module:{module_id}:exams")
    exams = []
    
    for exam_id in exam_ids:
        exam_data = r.get(f"exam:{exam_id}")
        if exam_data:
            exams.append(json.loads(exam_data))
    
    return exams
async def get_user_module_attempts(db: AsyncSession, user_id: int, module_id: UUID) -> int:
    """Count total exam attempts for this user and module"""
    result = await db.execute(
        select(func.count()).where(
            and_(
                UserExam.external_user_id == user_id,
                UserExam.module_id == module_id
            )
        )
    )
    return result.scalar() or 0



async def get_user_passed_exams_count(db: AsyncSession, user_id: int, module_id: UUID) -> int:
    """Count how many passed exams user has for this module"""
    result = await db.execute(
        select(func.count()).where(
            and_(
                UserExam.external_user_id == user_id,
                UserExam.module_id == module_id,
                UserExam.status == "passed"
            )
        )
    )
    return result.scalar() or 0


async def create_user_exam_from_redis(
    db: AsyncSession, 
    user_id: int, 
    module_id: UUID, 
    is_retake: bool = False,
    attempt_number: int = 1
):
    """
    Create exam in PostgreSQL using data from Redis
    """
    # Get exam data from Redis
    redis_exam = await get_exam_from_redis(user_id, module_id)
    
    if not redis_exam:
        raise ValueError("Exam not found in Redis")
    
    # Create exam in PostgreSQL
    new_exam = UserExam(
        id=UUID(redis_exam["exam_id"]),
        external_user_id=user_id,
        module_id=module_id,
        content=redis_exam["content"],
        supabase_urls=redis_exam.get("supabase_urls"),
        status=redis_exam.get("status", "generated"),
        total_questions=len(redis_exam["content"].get("questions", [])),
        is_retake=is_retake,
        attempt_number=attempt_number
    )
    
    db.add(new_exam)
    await db.commit()
    await db.refresh(new_exam)
    
    return new_exam





async def update_user_exam(db: AsyncSession, existing_exam: UserExam, exam_data: dict):
    if "content" in exam_data:
        existing_exam.content = exam_data["content"]
        existing_exam.total_questions = len(exam_data["content"].get("questions", []))
    if "status" in exam_data:
        existing_exam.status = exam_data["status"]
    if "score" in exam_data:
        existing_exam.score = exam_data["score"]
    if "correct_answers" in exam_data:
        existing_exam.correct_answers = exam_data["correct_answers"]
    if "time_spent" in exam_data:
        existing_exam.time_spent = exam_data["time_spent"]
    if "supabase_urls" in exam_data:
        existing_exam.supabase_urls = exam_data["supabase_urls"]
    
    await db.commit()
    await db.refresh(existing_exam)
    return existing_exam

async def get_user_exams(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(UserExam).where(UserExam.external_user_id == user_id)
    )
    return result.scalars().all()

async def get_module_exams_for_user(db: AsyncSession, user_id: int, module_id: UUID):
    result = await db.execute(
        select(UserExam).where(
            and_(
                UserExam.external_user_id == user_id,
                UserExam.module_id == module_id
            )
        )
    )
    return result.scalars().all()



async def update_user_exam_results(
    db: AsyncSession,
    exam_id: UUID,
    score: float,
    correct_answers: int,
    total_questions: int,
    time_spent: int,
    status: str = None
):
    """
    Update the results of a completed exam.
    """
    stmt = (
    update(UserExam)
    .where(UserExam.id == exam_id)
    .values(
        score=score,
        correct_answers=correct_answers,
        total_questions=total_questions,
        time_spent=time_spent,
        status=status if status else 'passed',
        completed_at=datetime.utcnow()
        )
    )
    await db.execute(stmt)
    await db.commit()

    # Fetch ORM object
    updated_exam = await db.get(UserExam, exam_id)
    return updated_exam