from typing import List, Dict, Any
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SemanticCacheMeta:
    embedding: List[float]
    extra: Dict[str, Any] = field(default_factory=dict)
