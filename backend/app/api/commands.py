"""Command execution endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.auth.jwt import verify_token
from app.auth.policy import can_execute
from app.services import device_service, audit_service
from app.ws.connection_manager import agent_connection_manager
from app import redis_client
import json
import uuid

router = APIRouter(prefix="/api/devices", tags=["commands"])

class CommandRequest(BaseModel):
    command: str
    params: Optional[dict] = None

class CommandResponse(BaseModel):
    command_id: str
    status: str
    message: str

@router.post("/{device_id}/command", response_model=CommandResponse)
async def execute_command(
    device_id: str,
    request: CommandRequest,
    db: AsyncSession = Depends(get_db),
    token: str = Query(...)
):
    """Execute a command on a device."""
    
    # Verify user token
    payload = verify_token(token)
    if not payload or payload.get("type") != "user":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("sub")
    user_role = payload.get("role")
    
    # Get device
    device = await device_service.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Check authorization
    if not can_execute(user_role, device_id, request.command):
        raise HTTPException(status_code=403, detail="Not authorized to execute this command")
    
    # Check if device is connected
    if not agent_connection_manager.is_connected(device_id):
        raise HTTPException(status_code=503, detail="Device not connected")
    
    # Send command to device
    command_id = str(uuid.uuid4())
    command_msg = {
        "type": "command",
        "id": command_id,
        "command": request.command,
        "params": request.params or {}
    }
    
    success = await agent_connection_manager.send_command(device_id, command_msg)
    if not success:
        raise HTTPException(status_code=503, detail="Failed to send command")
    
    # Log command execution
    await audit_service.log_action(
        db,
        device_id=device.id,
        action=request.command,
        status="pending",
        user_id=uuid.UUID(user_id),
        details={"command_id": command_id, "params": request.params}
    )
    
    return CommandResponse(
        command_id=command_id,
        status="sent",
        message="Command sent to device"
    )
