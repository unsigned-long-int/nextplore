from abc import ABC, abstractmethod
from uuid import UUID

from .encrypted_secret import EncryptedSecret


class CryptoClient(ABC):
    def __init__(self, kek_kid: str) -> None:
        self.kek_kid = kek_kid

    @abstractmethod
    def encrypt_secret(
        self, plaintext: str, aad: dict[str, str | UUID]
    ) -> EncryptedSecret: ...

    @abstractmethod
    def decrypt_secret(
        self,
        wrapped_dek: bytes,
        aad: dict[str, str | UUID],
        nonce: bytes,
        ciphertext: bytes,
        tag: bytes,
    ) -> str: ...
