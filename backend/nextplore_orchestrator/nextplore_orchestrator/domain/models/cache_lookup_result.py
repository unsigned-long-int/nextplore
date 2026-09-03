from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CacheLookupResult:
    embedding: list[float]
    json_payload: dict[str, Any] | None = field(default=None)

    @property
    def hit(self) -> bool:
        return self.json_payload is not Non
        e
