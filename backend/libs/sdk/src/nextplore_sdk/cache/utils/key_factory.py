import hashlib
from pydantic import BaseModel


def get_cache_key(model: BaseModel, *, prefix: str = '', salt: str = '') -> str:
    raw = model.model_dump_json()
    base = f'{salt}:{raw}' if salt else raw
    hash_digest = hashlib.sha256(base.encode()).hexdigest()
    return f'{prefix}:{hash_digest}' if prefix else hash_digest


def get_string_cache_key(value: str, *, prefix: str = '', salt: str = '') -> str:
    base = f'{salt}:{value}' if salt else value
    hash_digest = hashlib.sha256(base.encode()).hexdigest()
    return f'{prefix}:{hash_digest}' if prefix else hash_digest
