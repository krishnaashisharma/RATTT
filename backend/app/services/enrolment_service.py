"""Enrolment service."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.enrolment import EnrolmentToken
from datetime import datetime, timedelta
from app.config import settings
import secrets
import hashlib
import uuid

async def generate_enrolment_token(db: AsyncSession, created_by: uuid.UUID = None) -> str:
    """Generate a new enrolment token."""
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    expiry = datetime.utcnow() + timedelta(minutes=settings.ENROLMENT_TOKEN_EXPIRATION_MINUTES)
    
    enrolment_token = EnrolmentToken(
        token_hash=token_hash,
        expiry=expiry,
        created_by=created_by
    )
    db.add(enrolment_token)
    await db.commit()
    
    return token

async def validate_enrolment_token(db: AsyncSession, token: str) -> bool:
    """Validate an enrolment token."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    result = await db.execute(
        select(EnrolmentToken).where(EnrolmentToken.token_hash == token_hash)
    )
    enrolment_token = result.scalars().first()
    
    if not enrolment_token:
        return False
    
    if enrolment_token.used:
        return False
    
    if enrolment_token.expiry < datetime.utcnow():
        return False
    
    return True

async def mark_token_used(db: AsyncSession, token: str, device_id: str):
    """Mark an enrolment token as used."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    await db.execute(
        update(EnrolmentToken)
        .where(EnrolmentToken.token_hash == token_hash)
        .values(used=True, used_by_device_id=device_id)
    )
    await db.commit()
