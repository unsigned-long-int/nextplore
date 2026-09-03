from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SemanticMatch:
    json_payload: dict[str, Any]
