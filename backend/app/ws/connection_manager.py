"""WebSocket connection manager for agents."""
from typing import Dict, List
from fastapi import WebSocket
import json
from app import redis_client

class ConnectionManager:
    """Manages active WebSocket connections from agents."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, device_id: str):
        """Accept a new agent connection."""
        await websocket.accept()
        self.active_connections[device_id] = websocket
        await redis_client.publish(
            f"device_status:{device_id}",
            json.dumps({"status": "connected"})
        )
    
    def disconnect(self, device_id: str):
        """Remove a disconnected agent."""
        if device_id in self.active_connections:
            del self.active_connections[device_id]
    
    async def send_command(self, device_id: str, command: dict) -> bool:
        """Send a command to a device."""
        if device_id not in self.active_connections:
            return False
        
        try:
            websocket = self.active_connections[device_id]
            await websocket.send_json(command)
            return True
        except Exception as e:
            print(f"Error sending command to {device_id}: {e}")
            return False
    
    async def broadcast(self, message: str):
        """Broadcast a message to all connected agents."""
        for connection in self.active_connections.values():
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error broadcasting message: {e}")
    
    def get_connected_devices(self) -> List[str]:
        """Get list of connected device IDs."""
        return list(self.active_connections.keys())
    
    def is_connected(self, device_id: str) -> bool:
        """Check if a device is connected."""
        return device_id in self.active_connections

# Global instance
agent_connection_manager = ConnectionManager()
