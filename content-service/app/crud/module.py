from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from uuid import UUID
from sqlalchemy.orm import selectinload

from app.models.lesson import Lesson
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


from typing import List




async def get_full(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> List[Module]:
    stmt = (
        select(Module)
        .options(selectinload(Module.lessons))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    modules = result.scalars().unique().all()
    return modules

async def get_full_by_moduleid(db: AsyncSession, moduleid: UUID):
    stmt = (
        select(Module)
        .where(Module.id == moduleid)
        .options(selectinload(Module.lessons))  # Optional: eager load lessons
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_modules_with_lessons_and_files(db: AsyncSession, skip: int = 0, limit: int = 100):
    # 1. Récupérer modules + lessons + lessonfiles avec jointure
    result = await db.execute(
        select(Module).options(
            selectinload(Module.lessons).selectinload(Lesson.files)
        ).offset(skip).limit(limit)
    )
    modules = result.scalars().unique().all()

    # 2. Construire la structure JSON finale
    modules_list = []
    for module in modules:
        module_dict = {
            "id": str(module.id),
            "title": module.title,
            "name_fr": getattr(module, "name_fr", None),
            "description": module.description,
            "description_fr": getattr(module, "description_fr", None),
            "about": {
                "en": getattr(module, "about_en", None),
                "fr": getattr(module, "about_fr", None),
            },
            "image": getattr(module, "image", None),
            "lessons": [],
        }
        for lesson in module.lessons:
            # Extraire video et pdf des fichiers associés
            video_url = None
            pdf_url = None
            for f in lesson.files:
                if f.file_type.lower() == "video":
                    video_url = f.file_url
                elif f.file_type.lower() == "pdf":
                    pdf_url = f.file_url

            lesson_dict = {
                "id": str(lesson.id),
                "title": lesson.title,
                "title_fr": getattr(lesson, "title_fr", None),
                "completed": getattr(lesson, "completed", False),
                "video": video_url,
                "pdf": pdf_url,
            }
            module_dict["lessons"].append(lesson_dict)

        modules_list.append(module_dict)

    return modules_list
