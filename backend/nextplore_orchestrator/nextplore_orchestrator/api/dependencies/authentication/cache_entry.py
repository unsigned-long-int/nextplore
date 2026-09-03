from dataclasses import dataclass
from typing import Any


@dataclass
class CacheEntry:
    jwks: dict[str, Any]
    kid_index: dict[str, dict[str, Any]]
    expires_at: float
    etag: str | None = None
