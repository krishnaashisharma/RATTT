"""WebSocket endpoint for dashboard real-time updates."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import json
from app.database import get_db
from app.auth.jwt import verify_token
from app import redis_client

router = APIRouter(prefix="/ws", tags=["websocket"])

class DashboardConnectionManager:
    """Manages WebSocket connections from dashboard clients."""
    
    def __init__(self):
        self.active_connections: dict = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept a new dashboard connection."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
    
    def disconnect(self, user_id: str, websocket: WebSocket):
        """Remove a disconnected dashboard client."""
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def broadcast_to_user(self, user_id: str, message: dict):
        """Send a message to all dashboard connections for a user."""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error sending to dashboard: {e}")
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast to all connected dashboards."""
        for connections in self.active_connections.values():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error broadcasting: {e}")

# Global instance
dashboard_manager = DashboardConnectionManager()

@router.websocket("/dashboard")
async def websocket_dashboard(
    websocket: WebSocket,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """WebSocket endpoint for dashboard real-time updates."""
    
    # Verify token
    payload = verify_token(token)
    if not payload or payload.get("type") != "user":
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    user_id = payload.get("sub")
    
    # Accept connection
    await dashboard_manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive messages from dashboard (for future use)
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "subscribe":
                # Subscribe to device updates
                device_id = data.get("device_id")
                if device_id:
                    # Subscribe to Redis channel
                    pubsub = await redis_client.subscribe(f"device_status:{device_id}")
                    if pubsub:
                        async for message in pubsub.listen():
                            if message["type"] == "message":
                                await websocket.send_json({
                                    "type": "device_update",
                                    "device_id": device_id,
                                    "data": json.loads(message["data"]),
                                })
    
    except WebSocketDisconnect:
        dashboard_manager.disconnect(user_id, websocket)
    
    except Exception as e:
        print(f"Error in dashboard WebSocket: {e}")
        dashboard_manager.disconnect(user_id, websocket)

async def broadcast_device_update(device_id: str, status: str):
    """Broadcast device status update to all dashboards."""
    message = {
        "type": "device_status_change",
        "device_id": device_id,
        "status": status,
    }
    await dashboard_manager.broadcast_to_all(message)

async def broadcast_command_response(device_id: str, command_id: str, response: dict):
    """Broadcast command response to all dashboards."""
    message = {
        "type": "command_response",
        "device_id": device_id,
        "command_id": command_id,
        "response": response,
    }
    await dashboard_manager.broadcast_to_all(message)
