"""Device management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List
import uuid
import hashlib
from app.database import get_db
from app.services import device_service, enrolment_service
from app.auth.jwt import create_device_token, verify_token
from app.ws.connection_manager import agent_connection_manager

router = APIRouter(prefix="/api/devices", tags=["devices"])

class DeviceRegisterRequest(BaseModel):
    device_id: str
    os: str
    hostname: str
    enrolment_token: str
    public_key: str = None

class DeviceResponse(BaseModel):
    device_id: str
    os: str
    hostname: str
    status: str
    last_heartbeat: str = None
    
    class Config:
        from_attributes = True

class DeviceTokenResponse(BaseModel):
    device_token: str

@router.post("/register", response_model=DeviceTokenResponse)
async def register_device(
    request: DeviceRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register a new device."""
    
    # Validate enrolment token
    if not await enrolment_service.validate_enrolment_token(db, request.enrolment_token):
        raise HTTPException(status_code=403, detail="Invalid or expired enrolment token")
    
    # Check if device already exists
    existing_device = await device_service.get_device(db, request.device_id)
    if existing_device:
        raise HTTPException(status_code=409, detail="Device already registered")
    
    # Create device
    token_hash = hashlib.sha256(request.device_id.encode()).hexdigest()
    device = await device_service.create_device(
        db,
        device_id=request.device_id,
        os=request.os,
        hostname=request.hostname,
        token_hash=token_hash,
        public_key=request.public_key
    )
    
    # Mark enrolment token as used
    await enrolment_service.mark_token_used(db, request.enrolment_token, request.device_id)
    
    # Generate device JWT
    device_token = create_device_token(request.device_id, request.os)
    
    return DeviceTokenResponse(device_token=device_token)

@router.get("/", response_model=List[DeviceResponse])
async def list_devices(
    db: AsyncSession = Depends(get_db),
    token: str = Query(...)
):
    """List all devices."""
    
    # Verify user token
    payload = verify_token(token)
    if not payload or payload.get("type") != "user":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    devices = await device_service.get_all_devices(db)
    return devices

@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    token: str = Query(...)
):
    """Get device details."""
    
    # Verify user token
    payload = verify_token(token)
    if not payload or payload.get("type") != "user":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    device = await device_service.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return device

@router.post("/{device_id}/revoke")
async def revoke_device(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    token: str = Query(...)
):
    """Revoke a device."""
    
    # Verify user token
    payload = verify_token(token)
    if not payload or payload.get("type") != "user" or payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    device = await device_service.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    await device_service.delete_device(db, device_id)
    
    return {"message": "Device revoked"}

@router.get("/{device_id}/status")
async def get_device_status(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    token: str = Query(...)
):
    """Get device connection status."""
    
    # Verify user token
    payload = verify_token(token)
    if not payload or payload.get("type") != "user":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    device = await device_service.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    is_connected = agent_connection_manager.is_connected(device_id)
    
    return {
        "device_id": device_id,
        "status": device.status,
        "is_connected": is_connected,
        "last_heartbeat": device.last_heartbeat.isoformat() if device.last_heartbeat else None
    }
