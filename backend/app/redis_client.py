"""Redis client for pub/sub and caching."""
import redis.asyncio as redis
from app.config import settings
from typing import Optional

redis_client: Optional[redis.Redis] = None

async def init_redis():
    """Initialize Redis connection."""
    global redis_client
    redis_client = await redis.from_url(settings.REDIS_URL, decode_responses=True)
    await redis_client.ping()

async def close_redis():
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()

async def publish(channel: str, message: str):
    """Publish a message to a channel."""
    if redis_client:
        await redis_client.publish(channel, message)

async def subscribe(channel: str):
    """Subscribe to a channel."""
    if redis_client:
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(channel)
        return pubsub
    return None

async def get(key: str) -> Optional[str]:
    """Get a value from Redis."""
    if redis_client:
        return await redis_client.get(key)
    return None

async def set(key: str, value: str, ex: Optional[int] = None):
    """Set a value in Redis."""
    if redis_client:
        await redis_client.set(key, value, ex=ex)

async def delete(key: str):
    """Delete a key from Redis."""
    if redis_client:
        await redis_client.delete(key)
