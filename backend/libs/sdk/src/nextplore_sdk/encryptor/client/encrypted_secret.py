from uuid import UUID
from typing import Dict
from dataclasses import dataclass 


@dataclass(frozen=True)
class EncryptedSecret:
    nonce: bytes
    tag: bytes
    aad: Dict[str, str | UUID]
    ciphertext: bytes
    wrapped_dek: bytes
