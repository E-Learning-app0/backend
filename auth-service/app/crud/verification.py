# app/crud/verification.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.verification import EmailVerification
from sqlalchemy.future import select

async def save_verification_token(db: AsyncSession, user_id: str, token: str):
    verification = EmailVerification(token=token, utilisateur_id=user_id)
    db.add(verification)
    await db.commit()
    await db.refresh(verification)
    return verification

async def get_verification_by_token(db: AsyncSession, token: str):
    result = await db.execute(
        select(EmailVerification).where(EmailVerification.token == token)
    )
    return result.scalars().first()
