import os
from typing import Optional
from redis.asyncio import Redis


_redis_client: Optional[Redis] = None


def get_redis_client() -> Redis:
    global _redis_client
    if not _redis_client:
        redis_url = os.getenv('REDIS_URL', 'redis://redis:6379') 
        _redis_client = Redis.from_url(
            redis_url, 
            decode_responses=True,
            socket_timeout=1.0,
            socket_connect_timeout=1.0,
            max_connections=20
        )
    
    return _redis_client