"""WebSocket endpoint for agents."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
import json
from app.database import get_db
from app.models.device import Device
from app.models.audit import AuditLog
from app.auth.jwt import verify_token, refresh_device_token
from app.ws.connection_manager import agent_connection_manager
from app import redis_client

router = APIRouter(prefix="/ws", tags=["websocket"])

@router.websocket("/agent")
async def websocket_agent(
    websocket: WebSocket,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """WebSocket endpoint for agent connections."""
    
    # Verify token
    payload = verify_token(token)
    if not payload or payload.get("type") != "device":
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    device_id = payload.get("sub")
    os_type = payload.get("os")
    
    # Get device from database
    result = await db.execute(select(Device).where(Device.device_id == device_id))
    device = result.scalars().first()
    
    if not device:
        await websocket.close(code=4002, reason="Device not found")
        return
    
    # Accept connection and register
    await agent_connection_manager.connect(websocket, device_id)
    
    # Update device status
    await db.execute(
        update(Device)
        .where(Device.device_id == device_id)
        .values(status="connected", last_heartbeat=datetime.utcnow())
    )
    await db.commit()
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "heartbeat":
                # Update last heartbeat
                await db.execute(
                    update(Device)
                    .where(Device.device_id == device_id)
                    .values(last_heartbeat=datetime.utcnow())
                )
                await db.commit()
                
                # Publish heartbeat event
                await redis_client.publish(
                    f"device_heartbeat:{device_id}",
                    json.dumps({"device_id": device_id, "timestamp": datetime.utcnow().isoformat()})
                )
            
            elif msg_type == "command_response":
                # Log the command response
                command = data.get("command")
                status = data.get("status", "success")
                result = data.get("result")
                
                audit_log = AuditLog(
                    device_id=device.id,
                    action=command,
                    status=status,
                    details={"result": result}
                )
                db.add(audit_log)
                await db.commit()
                
                # Publish response to dashboard
                await redis_client.publish(
                    f"command_response:{device_id}",
                    json.dumps(data)
                )
            
            elif msg_type == "metrics":
                # Store metrics (optional)
                metrics = data.get("metrics")
                await redis_client.set(
                    f"device_metrics:{device_id}",
                    json.dumps(metrics),
                    ex=300  # 5 minute expiry
                )
            
            elif msg_type == "token_refresh_request":
                # Issue new device token
                new_token = refresh_device_token(device_id, os_type)
                await websocket.send_json({
                    "type": "token_refresh",
                    "new_token": new_token
                })
            
            elif msg_type == "consent_revoked":
                # Device revoked consent
                await db.execute(
                    update(Device)
                    .where(Device.device_id == device_id)
                    .values(status="disconnected")
                )
                await db.commit()
                break
            
            elif msg_type == "consent_paused":
                # Device paused
                await db.execute(
                    update(Device)
                    .where(Device.device_id == device_id)
                    .values(status="paused")
                )
                await db.commit()
    
    except WebSocketDisconnect:
        agent_connection_manager.disconnect(device_id)
        await db.execute(
            update(Device)
            .where(Device.device_id == device_id)
            .values(status="disconnected")
        )
        await db.commit()
        await redis_client.publish(
            f"device_status:{device_id}",
            json.dumps({"status": "disconnected"})
        )
    
    except Exception as e:
        print(f"Error in agent WebSocket: {e}")
        agent_connection_manager.disconnect(device_id)
        await db.execute(
            update(Device)
            .where(Device.device_id == device_id)
            .values(status="error")
        )
        await db.commit()
