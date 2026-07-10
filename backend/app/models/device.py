"""Device model."""
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum
from app.database import Base

class DeviceStatus(str, enum.Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    PAUSED = "paused"
    ERROR = "error"

class Device(Base):
    __tablename__ = "devices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(String(255), unique=True, nullable=False, index=True)
    os = Column(String(50), nullable=False)
    hostname = Column(String(255), nullable=False)
    status = Column(SQLEnum(DeviceStatus), default=DeviceStatus.DISCONNECTED, nullable=False)
    last_heartbeat = Column(DateTime, nullable=True)
    token_hash = Column(String(255), nullable=False)
    public_key = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Device {self.device_id}>"
