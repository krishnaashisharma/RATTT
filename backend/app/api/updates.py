"""Update management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.auth.jwt import verify_token
from app.models.update import UpdateArtifact
import uuid

router = APIRouter(prefix="/api/updates", tags=["updates"])

class UpdateCheckResponse(BaseModel):
    available: bool
    version: Optional[str] = None
    url: Optional[str] = None
    checksum: Optional[str] = None
    signature: Optional[str] = None

class UpdateArtifactRequest(BaseModel):
    version: str
    platform: str
    binary_url: str
    checksum: str
    signature: str
    rollout_percentage: int = 100

@router.get("/check", response_model=UpdateCheckResponse)
async def check_for_updates(
    version: str = Query(...),
    platform: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Check for available updates."""
    
    # Get the latest update artifact for this platform
    result = await db.execute(
        select(UpdateArtifact)
        .where(UpdateArtifact.platform == platform)
        .order_by(UpdateArtifact.created_at.desc())
        .limit(1)
    )
    artifact = result.scalars().first()
    
    if not artifact or artifact.version <= version:
        return UpdateCheckResponse(available=False)
    
    return UpdateCheckResponse(
        available=True,
        version=artifact.version,
        url=artifact.binary_url,
        checksum=artifact.checksum,
        signature=artifact.signature
    )

@router.post("/artifact")
async def upload_update_artifact(
    request: UpdateArtifactRequest,
    db: AsyncSession = Depends(get_db),
    token: str = Query(...)
):
    """Upload a new update artifact (admin only)."""
    
    # Verify user token
    payload = verify_token(token)
    if not payload or payload.get("type") != "user" or payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Create update artifact
    artifact = UpdateArtifact(
        version=request.version,
        platform=request.platform,
        binary_url=request.binary_url,
        checksum=request.checksum,
        signature=request.signature,
        rollout_percentage=request.rollout_percentage
    )
    db.add(artifact)
    await db.commit()
    
    return {"message": "Update artifact created", "id": str(artifact.id)}
