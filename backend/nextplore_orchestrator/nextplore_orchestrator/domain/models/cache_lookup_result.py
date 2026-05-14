from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

@dataclass(frozen=True)
class CacheLookupResult:
    embedding: List[float]
    json_payload: Optional[Dict[str, Any]] = field(default=None)


    @property
    def hit(self) -> bool:
        return self.json_payload is not Non
        e