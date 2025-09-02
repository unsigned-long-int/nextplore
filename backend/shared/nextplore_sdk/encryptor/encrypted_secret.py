from dataclasses import dataclass 


@dataclass(frozen=True)
class EncryptedSecret:
    nonce: bytes
    tag: bytes
    aad: bytes
    ciphertext: bytes
    wrapped_dek: bytes
