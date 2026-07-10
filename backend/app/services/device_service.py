"""Device service."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.device import Device
import uuid

async def get_device(db: AsyncSession, device_id: str) -> Device:
    """Get a device by ID."""
    result = await db.execute(select(Device).where(Device.device_id == device_id))
    return result.scalars().first()

async def get_all_devices(db: AsyncSession) -> list:
    """Get all devices."""
    result = await db.execute(select(Device))
    return result.scalars().all()

async def create_device(
    db: AsyncSession,
    device_id: str,
    os: str,
    hostname: str,
    token_hash: str,
    public_key: str = None
) -> Device:
    """Create a new device."""
    device = Device(
        device_id=device_id,
        os=os,
        hostname=hostname,
        token_hash=token_hash,
        public_key=public_key,
        status="disconnected"
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device

async def update_device_status(db: AsyncSession, device_id: str, status: str):
    """Update device status."""
    await db.execute(
        update(Device)
        .where(Device.device_id == device_id)
        .values(status=status)
    )
    await db.commit()

async def delete_device(db: AsyncSession, device_id: str):
    """Delete a device."""
    device = await get_device(db, device_id)
    if device:
        await db.delete(device)
        await db.commit()
