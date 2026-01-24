from typing import Dict
from uuid import UUID
from abc import ABC, abstractmethod

from .encrypted_secret import EncryptedSecret


class CryptoClient(ABC):
    def __init__(self, kek_kid: str) -> None:
        self.kek_kid = kek_kid
        
    @abstractmethod
    def encrypt_secret(self, plaintext: str, aad: Dict[str, str | UUID]) -> EncryptedSecret: ...

    @abstractmethod
    def decrypt_secret(
            self,
            wrapped_dek: bytes,
            aad: Dict[str, str | UUID],
            nonce: bytes,
            ciphertext: bytes,
            tag: bytes
    ) -> str: ...
    