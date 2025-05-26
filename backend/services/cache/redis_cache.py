import redis 
import json 

from typing import List, Dict, Any

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

def cache_orm_vectors(
        cache_key: str, 
        orm_vectors: List[Dict[str, Any]], 
        ttl: int = 86400
        ) -> None:
    pass
    