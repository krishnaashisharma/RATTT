"""Update artifact model."""
from sqlalchemy import Column, String, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.database import Base

class UpdateArtifact(Base):
    __tablename__ = "update_artifacts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version = Column(String(20), nullable=False, index=True)
    platform = Column(String(50), nullable=False, index=True)  # macos, windows
    binary_url = Column(String(500), nullable=False)
    checksum = Column(String(255), nullable=False)  # SHA-256
    signature = Column(Text, nullable=False)  # Ed25519 signature
    rollout_percentage = Column(Integer, default=100, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<UpdateArtifact {self.version}-{self.platform}>"
