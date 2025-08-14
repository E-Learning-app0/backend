from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from app.schemas.user import CurrentUser
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.db.session import get_db
from app.models.user_progress import UserProgress
from app.models.module import Module
from app.schemas.user_progress import (
    UserProgressCreate,
    UserProgressUpdate,
    UserProgress,
    UserProgressWithModule,
    ModuleWithUnlockStatus
)
from typing import List
from app.api.deps import get_current_user
from app.crud.crud_user_progress import get_user_progress_with_module, get_user_progress_by_semester, unlock_module,get_user_progress,get_modules_with_unlock_status

router = APIRouter(prefix="/userprogress", tags=["Users_Progress"])



@router.get("/modulesProgress", response_model=List[ModuleWithUnlockStatus])
async def list_modules_with_unlock_status(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.id
    return await get_modules_with_unlock_status(db, user_id)


@router.post("/", response_model=UserProgress, status_code=status.HTTP_201_CREATED)
def create_user_progress(
    user_progress: UserProgressCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create new user progress record
    """
    # Verify module exists
    module = db.query(Module).filter(Module.id == user_progress.module_id).first()
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )
    
    # Check if progress already exists
    existing_progress = get_user_progress(
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
        new_progress = UserProgress(
            external_user_id=current_user.id,
            module_id=user_progress.module_id,
            is_module_unlocked=user_progress.is_module_unlocked,
            last_accessed=datetime.utcnow()
        )
        db.add(new_progress)
        db.commit()
        db.refresh(new_progress)
        return new_progress
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )




@router.get("/test/{module_id}")
def test_uuid_validation(
    module_id: UUID = Path(...)
):
    print(f"Successfully received UUID: {module_id}")
    return {"module_id": str(module_id), "type": str(type(module_id))}

@router.get("/{module_id}", response_model=UserProgressWithModule)
async def get_user_progress_router(
    module_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    print(f"Fetching progress for user_id={current_user.id}, module_id={module_id}")
    progress = await get_user_progress_with_module(
        db,
        user_id=current_user.id,
        module_id=module_id
    )
    print(f"Progress found: {progress}")
    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found")
    return progress


@router.patch("/{module_id}", response_model=UserProgress)
def update_progress(
    module_id: uuid.UUID,
    update_data: UserProgressUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update user progress (partial update)
    """
    progress = get_user_progress(
        db,
        user_id=current_user.id,
        module_id=module_id
    )
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Progress not found"
        )
    
    try:
        if update_data.is_module_unlocked is not None:
            progress.is_module_unlocked = update_data.is_module_unlocked
        if update_data.is_module_completed is not None:
            progress.is_module_completed = update_data.is_module_completed
            if update_data.is_module_completed:
                progress.completed_at = datetime.utcnow()
        
        progress.last_accessed = datetime.utcnow()
        db.commit()
        db.refresh(progress)
        return progress
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{module_id}/unlock", response_model=UserProgress)
def unlock_module(
    module_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Unlock a module for the current user
    """
    return unlock_module(
        db,
        user_id=current_user.id,
        module_id=module_id
    )

@router.get("/semester/{semester}", response_model=list[UserProgressWithModule])
async def get_semester_progress(
    semester: str,
    db: AsyncSession = Depends(get_db),  # Changed to AsyncSession
    current_user: dict = Depends(get_current_user)
):
    """
    Get all progress records for a specific semester
    """
    progress = await get_user_progress_by_semester(
        db,
        user_id=current_user.id,
        semester=semester
    )
    return progress


@router.post("/{module_id}/complete", response_model=UserProgress)
async def complete_module(
    module_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    progress = await get_user_progress(
        db,
        user_id=current_user.id,
        module_id=module_id
    )
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Progress record not found"
        )
    
    progress.is_module_completed = True
    progress.completed_at = datetime.utcnow()
    progress.last_accessed = datetime.utcnow()

    try:
        db.commit()
        db.refresh(progress)
        return progress
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )



from app.services.progress_utils import try_unlock_next_semester_async

@router.post("/unlock-next/{current_semester}")
async def unlock_next_semester(
    current_semester: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    result = await try_unlock_next_semester_async(
        db=db,
        user_id=current_user.id,
        current_semester=current_semester
    )
    return result

