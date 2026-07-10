"""JWT token creation and verification."""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from app.config import settings
import uuid

def create_user_token(user_id: uuid.UUID, role: str) -> str:
    """Create a JWT token for a user."""
    expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    to_encode = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
        "type": "user",
    }
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def create_device_token(device_id: str, os_type: str) -> str:
    """Create a JWT token for a device."""
    expire = datetime.utcnow() + timedelta(hours=settings.DEVICE_JWT_EXPIRATION_HOURS)
    to_encode = {
        "sub": device_id,
        "os": os_type,
        "exp": expire,
        "type": "device",
    }
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None

def refresh_device_token(device_id: str, os_type: str) -> str:
    """Refresh a device token."""
    return create_device_token(device_id, os_type)
