from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class CacheEntry:
    jwks: Dict[str, Any]
    kid_index: Dict[str, Dict[str, Any]]
    expires_at: float
    etag: Optional[str] = None
