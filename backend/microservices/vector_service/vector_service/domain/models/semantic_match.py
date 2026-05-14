from typing import Dict, Any 
from dataclasses import dataclass


@dataclass(frozen=True)
class SemanticMatch:
    json_payload: Dict[str, Any]
