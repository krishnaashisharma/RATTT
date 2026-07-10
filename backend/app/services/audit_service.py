"""Audit service."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.audit import AuditLog
from app.models.device import Device
import uuid

async def log_action(
    db: AsyncSession,
    device_id: uuid.UUID,
    action: str,
    status: str = "success",
    user_id: uuid.UUID = None,
    details: dict = None
):
    """Log an action to the audit trail."""
    audit_log = AuditLog(
        device_id=device_id,
        action=action,
        status=status,
        user_id=user_id,
        details=details
    )
    db.add(audit_log)
    await db.commit()

async def get_audit_logs(
    db: AsyncSession,
    device_id: uuid.UUID = None,
    limit: int = 100,
    offset: int = 0
) -> list:
    """Get audit logs."""
    query = select(AuditLog)
    
    if device_id:
        query = query.where(AuditLog.device_id == device_id)
    
    query = query.order_by(AuditLog.timestamp.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    return result.scalars().all()
