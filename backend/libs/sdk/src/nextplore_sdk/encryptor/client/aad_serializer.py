import json
from uuid import UUID
from typing import Dict

def serialize_aad(aad: Dict[str, str | UUID]) -> bytes:
    serializable_aad = {
        key: str(value) if isinstance(value, UUID) else value
        for key, value in aad.items()
    }
    return json.dumps(serializable_aad, separators=(',', ':')).encode()
