from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload, joinedload
from app.schemas.user import CurrentUser
from datetime import datetime
import uuid
from uuid import UUID
from app.db.session import get_db
from app.models.user_progress import UserProgress
from app.models.module import Module
from app.schemas.user_progress import (
    UserProgressCreate,
    UserProgressUpdate,
    UserProgress as UserProgressSchema,
    UserProgressWithModule,
    ModuleWithUnlockStatus
)
from typing import List, Optional
from app.api.deps import get_current_user
from app.crud.crud_user_progress import (
    get_user_progress_with_module, 
    get_user_progress_by_semester, 
    get_all_user_progress,
    get_all_users_progress,
    unlock_module,
    get_user_progress,
    get_modules_with_unlock_status,
    update_user_progress,
    create_user_progress,
    delete_user_progress,
    get_semester_completion_status,
    is_module_unlocked_for_user,
    calculate_module_progress_percentage,
    update_module_progress_percentage,
    check_and_unlock_next_semester,
    get_user_dashboard_progress,
    unlock_semester_modules,
    get_current_semester,
    is_semester_accessible
)

router = APIRouter(prefix="/userprogress", tags=["User_Progress"])

# CREATE USER PROGRESS
@router.post("/", response_model=UserProgressSchema, status_code=status.HTTP_201_CREATED)
async def create_progress(
    user_progress: UserProgressCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create new user progress record"""
    # Check if module exists
    result = await db.execute(select(Module).where(Module.id == user_progress.module_id))
    module = result.scalars().first()
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )
    
    # Check if progress already exists
    existing_progress = await get_user_progress(
        db, 
        user_id=current_user.id,
        module_id=user_progress.module_id
    )
    if existing_progress:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Progress record already exists"
        )
    
    try:
        progress = await create_user_progress(
            db,
            user_id=current_user.id,
            module_id=user_progress.module_id,
            is_module_unlocked=user_progress.is_module_unlocked
        )
        return progress
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# GET USER PROGRESS BY USER ID
@router.get("/", response_model=List[UserProgressWithModule])
async def get_user_progress_list(
    user_id: Optional[int] = Query(None),
    module_id: Optional[UUID] = Query(None),
    semester: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get user progress with various filters:
    - ?user_id={userId} - Get progress for specific user
    - ?module_id={moduleId} - Get progress for specific module  
    - ?semester={semester} - Get progress for specific semester
    - No params - Get all progress for current user
    """
    
    # If user_id is provided, use it; otherwise use current user
    target_user_id = user_id if user_id is not None else current_user.id
    
    if module_id:
        # Get progress for specific module
        progress = await get_user_progress_with_module(db, target_user_id, module_id)
        return [progress] if progress else []
    
    elif semester:
        # Get progress for specific semester
        progress_list = await get_user_progress_by_semester(db, target_user_id, semester)
        return progress_list
    
    else:
        # Get all progress for user
        progress_list = await get_all_user_progress(db, target_user_id)
        return progress_list


# UPDATE USER PROGRESS
@router.put("/{progress_id}", response_model=UserProgressSchema)
async def update_progress(
    progress_id: UUID,  # This should be module_id based on frontend usage
    update_data: UserProgressUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update user progress (treating progress_id as module_id)"""
    
    # Convert UserProgressUpdate to dict, excluding None values
    update_dict = {}
    if update_data.is_module_unlocked is not None:
        update_dict['is_module_unlocked'] = update_data.is_module_unlocked
    if update_data.is_module_completed is not None:
        update_dict['is_module_completed'] = update_data.is_module_completed
        if update_data.is_module_completed:
            update_dict['completed_at'] = datetime.utcnow()
    if update_data.progress_percentage is not None:
        update_dict['progress_percentage'] = update_data.progress_percentage
    if update_data.last_accessed is not None:
        update_dict['last_accessed'] = update_data.last_accessed
    
    progress = await update_user_progress(
        db,
        user_id=current_user.id,
        module_id=progress_id,  # treating progress_id as module_id
        update_data=update_dict
    )
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Progress not found"
        )
    
    return progress


# DELETE USER PROGRESS
@router.delete("/{progress_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_progress(
    progress_id: UUID,  # This should be module_id based on frontend usage
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete user progress (treating progress_id as module_id)"""
    success = await delete_user_progress(
        db,
        user_id=current_user.id,
        module_id=progress_id  # treating progress_id as module_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Progress not found"
        )


# UNLOCK MODULE
@router.post("/{progress_id}/unlock", response_model=UserProgressSchema)
async def unlock_module_endpoint(
    progress_id: UUID,  # This should be module_id based on frontend usage
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Unlock a module for the current user"""
    try:
        progress = await unlock_module(
            db,
            user_id=current_user.id,
            module_id=progress_id  # treating progress_id as module_id
        )
        return progress
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# CHECK SEMESTER COMPLETION
@router.get("/semester/{semester}/completion")
async def check_semester_completion(
    semester: str,
    user_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Check if a semester is completed for a user"""
    target_user_id = user_id if user_id is not None else current_user.id
    
    try:
        # Get all modules in the semester
        result = await db.execute(
            select(Module).where(Module.semester == semester)
        )
        semester_modules = result.scalars().all()
        
        if not semester_modules:
            return {"completed": False, "reason": "No modules found for semester"}
        
        # Check how many modules are completed
        completed_count = 0
        total_count = len(semester_modules)
        
        for module in semester_modules:
            progress = await get_user_progress(db, target_user_id, module.id)
            if progress and progress.is_module_completed:
                completed_count += 1
        
        is_completed = completed_count == total_count
        completion_percentage = (completed_count / total_count * 100) if total_count > 0 else 0
        
        return {
            "completed": is_completed,
            "semester": semester,
            "completed_modules": completed_count,
            "total_modules": total_count,
            "completion_percentage": completion_percentage
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# LEGACY ENDPOINTS - Keep for backward compatibility
@router.get("/allusers", response_model=List[ModuleWithUnlockStatus])
async def list_all_users_progress(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all users progress - Admin only"""
    return await get_all_users_progress(db)


@router.get("/modulesProgress", response_model=List[ModuleWithUnlockStatus])
async def list_modules_with_unlock_status(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all modules with unlock status for current user"""
    user_id = current_user.id
    return await get_modules_with_unlock_status(db, user_id)


# ADDITIONAL UTILITY ENDPOINTS
@router.post("/{module_id}/complete", response_model=UserProgressSchema)
async def complete_module(
    module_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mark a module as completed"""
    update_dict = {
        'is_module_completed': True,
        'completed_at': datetime.utcnow(),
        'progress_percentage': 100,
        'last_accessed': datetime.utcnow()
    }
    
    progress = await update_user_progress(
        db,
        user_id=current_user.id,
        module_id=module_id,
        update_data=update_dict
    )
    
    if not progress:
        # Create new progress if doesn't exist
        progress = await create_user_progress(
            db,
            user_id=current_user.id,
            module_id=module_id,
            is_module_unlocked=True
        )
        
        # Update with completion data
        progress = await update_user_progress(
            db,
            user_id=current_user.id,
            module_id=module_id,
            update_data=update_dict
        )
    
    return progress


# DASHBOARD PROGRESS ENDPOINT
@router.get("/dashboard/progress")
async def get_dashboard_progress(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive progress data for user dashboard"""
    return await get_user_dashboard_progress(db, current_user.id)


# UPDATE PROGRESS PERCENTAGE
@router.post("/{module_id}/progress/{percentage}")
async def update_progress_percentage(
    module_id: UUID,
    percentage: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update module progress percentage"""
    if not (0 <= percentage <= 100):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Percentage must be between 0 and 100"
        )
    
    progress = await update_module_progress_percentage(
        db, current_user.id, module_id, percentage
    )
    return progress


# INITIALIZE USER PROGRESS (for first-time users)
@router.post("/initialize")
async def initialize_user_progress(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Initialize progress for a new user - unlock S1 modules"""
    try:
        # Check if user already has progress
        existing_progress = await get_all_user_progress(db, current_user.id)
        
        if existing_progress:
            return {
                "message": "User progress already initialized",
                "modules_count": len(existing_progress)
            }
        
        # Unlock all S1 modules for new user
        await unlock_semester_modules(db, current_user.id, "S1")
        
        # Get updated progress count
        new_progress = await get_all_user_progress(db, current_user.id)
        
        return {
            "message": "User progress initialized successfully",
            "unlocked_semester": "S1",
            "modules_unlocked": len(new_progress)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize user progress: {str(e)}"
        )


# GET CURRENT USER STATS
@router.get("/stats")
async def get_user_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get user progress statistics"""
    try:
        dashboard_data = await get_user_dashboard_progress(db, current_user.id)
        current_semester = await get_current_semester(db, current_user.id)
        
        return {
            "user_id": current_user.id,
            "current_semester": current_semester,
            "total_modules_completed": dashboard_data["total_modules_completed"],
            "total_modules": dashboard_data["total_modules"],
            "overall_completion_percentage": (
                (dashboard_data["total_modules_completed"] / dashboard_data["total_modules"] * 100)
                if dashboard_data["total_modules"] > 0 else 0
            ),
            "semester_stats": dashboard_data["semester_stats"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user stats: {str(e)}"
        )


# UNLOCK SEMESTER
@router.post("/semester/{semester}/unlock")
async def unlock_semester(
    semester: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Manually unlock a semester (admin or special cases)"""
    if semester not in ["S1", "S2", "S3", "S4"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid semester. Must be S1, S2, S3, or S4"
        )
    
    await unlock_semester_modules(db, current_user.id, semester)
    return {"message": f"Semester {semester} unlocked successfully"}


from app.services.progress_utils import try_unlock_next_semester_async

@router.post("/unlock-next/{current_semester}")
async def unlock_next_semester(
    current_semester: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Unlock the next semester if current is completed"""
    result = await try_unlock_next_semester_async(
        db=db,
        user_id=current_user.id,
        current_semester=current_semester
    )
    return result