# app/services/audit.py
from app.models.journal_audit import JournalAudit
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

async def log_action(db: AsyncSession, utilisateur_id: int, action: str, details: str = ""):
    log = JournalAudit(
        utilisateur_id=utilisateur_id,
        action=action,
        horodatage=datetime.utcnow(),
        details=details,
    )
    db.add(log)
    await db.commit()
