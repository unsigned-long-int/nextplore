from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class EncryptedSecret:
    nonce: bytes
    tag: bytes
    aad: dict[str, str | UUID]
    ciphertext: bytes
    wrapped_dek: bytes
