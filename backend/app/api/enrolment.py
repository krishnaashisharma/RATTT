"""Enrolment token management."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database import get_db
from app.services import enrolment_service
from app.auth.jwt import verify_token

router = APIRouter(prefix="/api/enrolment", tags=["enrolment"])

class EnrolmentTokenResponse(BaseModel):
    token: str
    expiry_minutes: int

@router.post("/generate", response_model=EnrolmentTokenResponse)
async def generate_enrolment_token(
    db: AsyncSession = Depends(get_db),
    token: str = Query(...)
):
    """Generate a new enrolment token (admin only)."""
    
    # Verify user token
    payload = verify_token(token)
    if not payload or payload.get("type") != "user" or payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Generate token
    enrolment_token = await enrolment_service.generate_enrolment_token(db)
    
    from app.config import settings
    return EnrolmentTokenResponse(
        token=enrolment_token,
        expiry_minutes=settings.ENROLMENT_TOKEN_EXPIRATION_MINUTES
    )
