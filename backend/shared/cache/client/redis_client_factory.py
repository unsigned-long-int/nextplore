import os
from redis.asyncio import Redis


_redis_client: Redis = None

def get_redis_client() -> Redis:
    global _redis_client
    if not _redis_client:
        redis_url = os.getenv('REDIS_URL', 'redis://redis:6379') 
        _redis_client = Redis.from_url(redis_url, decode_responses=True)
    
    return _redis_client