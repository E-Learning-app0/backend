from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from uuid import UUID

from app.models.module import Module

async def get_module(db: AsyncSession, module_id: UUID) -> Module | None:
    result = await db.execute(select(Module).where(Module.id == module_id))
    return result.scalar_one_or_none()

async def get_modules(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Module]:
    result = await db.execute(select(Module).offset(skip).limit(limit))
    return result.scalars().all()

async def create_module(db: AsyncSession, module_data) -> Module:
    new_module = Module(**module_data.dict())
    db.add(new_module)
    await db.commit()
    await db.refresh(new_module)
    return new_module

async def update_module(db: AsyncSession, module_id: UUID, update_data) -> Module | None:
    module = await get_module(db, module_id)
    if not module:
        return None
    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(module, key, value)
    await db.commit()
    await db.refresh(module)
    return module

async def delete_module(db: AsyncSession, module_id: UUID) -> bool:
    module = await get_module(db, module_id)
    if not module:
        return False
    await db.delete(module)
    await db.commit()
    return True
