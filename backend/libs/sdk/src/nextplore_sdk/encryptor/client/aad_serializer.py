import json
from uuid import UUID


def serialize_aad(aad: dict[str, str | UUID]) -> bytes:
    serializable_aad = {
        key: str(value) if isinstance(value, UUID) else value
        for key, value in aad.items()
    }
    return json.dumps(serializable_aad, separators=(",", ":")).encode()
