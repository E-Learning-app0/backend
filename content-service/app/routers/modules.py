from fastapi import APIRouter, Depends, HTTPException, status,Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.schemas.module import ModuleRead, ModuleCreate, ModuleUpdate,ModuleReadCustom
from app.crud.module import get_modules, create_module, update_module, delete_module,get_full,get_full_by_moduleid
from app.dependencies.roles import require_any_role
from app.models import Module  # Assurez-vous que le modèle Module est importé correctement

router = APIRouter(prefix="/modules", tags=["Modules"])

@router.get("/", response_model=List[ModuleRead])
async def read_modules(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_any_role("admin", "teacher", "student"))  # 👈 all can view
):
    return await get_modules(db, skip=skip, limit=limit)


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

@router.get("/full", response_model=List[ModuleReadCustom])
async def read_full(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    # This already returns a list of Module objects
    modules = await get_full(db, skip, limit)
    
    # Convert SQLAlchemy models to Pydantic models
    return [ModuleReadCustom.model_validate(module) for module in modules]


@router.get("/full/{moduleid}", response_model=List[ModuleReadCustom])
async def read_full_by_moduleid(
    moduleid: UUID = Path(..., description="ID of the module"),
    db: AsyncSession = Depends(get_db)
):
    modules = await get_full_by_moduleid(db, moduleid)
    return [ModuleReadCustom.model_validate(module) for module in modules]


"""

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
"""