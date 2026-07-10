"""User authentication endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database import get_db
from app.auth.jwt import create_user_token
from app.models.user import User, UserRole
from sqlalchemy import select
import hashlib
import uuid

router = APIRouter(prefix="/api/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    role: str

async def hash_password(password: str) -> str:
    """Hash a password."""
    return hashlib.sha256(password.encode()).hexdigest()

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """User login."""
    
    # Get user from database
    result = await db.execute(select(User).where(User.username == request.username))
    user = result.scalars().first()
    
    if not user:
        # For demo purposes, create a default admin user
        if request.username == "admin" and request.password == "admin":
            hashed_password = await hash_password(request.password)
            user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=hashed_password,
                role=UserRole.ADMIN
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    else:
        # Verify password
        hashed_password = await hash_password(request.password)
        if user.hashed_password != hashed_password:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create JWT token
    access_token = create_user_token(user.id, user.role.value)
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=str(user.id),
        role=user.role.value
    )
