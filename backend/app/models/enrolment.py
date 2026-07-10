"""Enrolment token model."""
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.database import Base

class EnrolmentToken(Base):
    __tablename__ = "enrolment_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    used = Column(Boolean, default=False, nullable=False)
    used_by_device_id = Column(String(255), nullable=True)
    expiry = Column(DateTime, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<EnrolmentToken {self.id}>"
