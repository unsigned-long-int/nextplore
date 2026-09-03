from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SemanticCacheMeta:
    embedding: list[float]
    extra: dict[str, Any] = field(default_factory=dict)
