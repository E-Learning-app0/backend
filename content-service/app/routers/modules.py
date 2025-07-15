from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.schemas.module import ModuleRead, ModuleCreate, ModuleUpdate
from app.crud.module import get_module, get_modules, create_module, update_module, delete_module
from app.dependencies.roles import require_any_role

router = APIRouter(prefix="/modules", tags=["Modules"])

@router.get("/", response_model=List[ModuleRead])
async def read_modules(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_any_role("admin", "teacher", "student"))  # 👈 all can view
):
    return await get_modules(db, skip=skip, limit=limit)

@router.get("/{module_id}", response_model=ModuleRead)
async def read_module(
    module_id: UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_any_role("admin", "teacher", "student"))
):
    module = await get_module(db, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return module

@router.post("/", response_model=ModuleRead, status_code=status.HTTP_201_CREATED)
async def create_new_module(
    module_in: ModuleCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_any_role("admin", "teacher"))  # 👈 only admin & teacher
):
    return await create_module(db, module_in)

@router.put("/{module_id}", response_model=ModuleRead)
async def update_existing_module(
    module_id: UUID,
    module_in: ModuleUpdate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_any_role("admin", "teacher"))
):
    updated_module = await update_module(db, module_id, module_in)
    if not updated_module:
        raise HTTPException(status_code=404, detail="Module not found")
    return updated_module

@router.delete("/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_module(
    module_id: UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_any_role("admin")) 
):
    success = await delete_module(db, module_id)
    if not success:
        raise HTTPException(status_code=404, detail="Module not found")
    return
