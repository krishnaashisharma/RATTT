"""Audit log endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
from app.database import get_db
from app.auth.jwt import verify_token
from app.services import audit_service, device_service
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/audit", tags=["audit"])

class AuditLogResponse(BaseModel):
    id: str
    device_id: str
    action: str
    status: str
    timestamp: str
    details: Optional[dict] = None
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[AuditLogResponse])
async def get_audit_logs(
    device_id: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Get audit logs."""
    
    # Verify user token
    payload = verify_token(token)
    if not payload or payload.get("type") != "user":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    device_uuid = None
    if device_id:
        device = await device_service.get_device(db, device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        device_uuid = device.id
    
    logs = await audit_service.get_audit_logs(
        db,
        device_id=device_uuid,
        limit=limit,
        offset=offset
    )
    
    return [
        AuditLogResponse(
            id=str(log.id),
            device_id=str(log.device_id),
            action=log.action,
            status=log.status,
            timestamp=log.timestamp.isoformat(),
            details=log.details
        )
        for log in logs
    ]
