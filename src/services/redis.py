import redis
from src.config import get_settings


# =============================================================================
# Redis Key Constants
# =============================================================================

class RedisKeys:
    """Centralized Redis key definitions."""
    API_HOST = "api_host"
    ORG_ID = "org_id"


class RedisClient:
    def __init__(self):
        settings = get_settings()
        url = settings.redis_url
        self.client = redis.Redis.from_url(url, decode_responses=True)

    def set(self, key: str, value: str, expire: int = None) -> bool:
        """Set a key-value pair in Redis."""
        return self.client.setex(key, expire, value) if expire else self.client.set(key, value)

    def get(self, key: str) -> str | None:
        """Get a value by key from Redis."""
        return self.client.get(key)

    def delete(self, key: str) -> int:
        """Delete a key from Redis."""
        return self.client.delete(key)

    def ping(self) -> bool:
        """Test Redis connection."""
        try:
            return self.client.ping()
        except redis.ConnectionError:
            return False


def get_redis_client() -> RedisClient:
    """Get a Redis client instance."""
    return RedisClient()


# =============================================================================
# Context Accessors
# =============================================================================

def get_api_host() -> str | None:
    """Get the stored API host."""
    return get_redis_client().get(RedisKeys.API_HOST)


def get_org_id() -> str | None:
    """Get the stored organization ID."""
    return get_redis_client().get(RedisKeys.ORG_ID)


def set_api_host(value: str) -> bool:
    """Store the API host."""
    return get_redis_client().set(RedisKeys.API_HOST, value)


def set_org_id(value: str) -> bool:
    """Store the organization ID."""
    return get_redis_client().set(RedisKeys.ORG_ID, value)
