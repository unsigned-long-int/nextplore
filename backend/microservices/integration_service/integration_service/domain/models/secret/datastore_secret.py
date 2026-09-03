from dataclasses import dataclass, field
from uuid import UUID

from nextplore_sdk.encryptor.client.crypto_client import CryptoClient


@dataclass(frozen=True)
class DataStoreSecret:
    organization_id: UUID
    user_id: UUID
    datastore_id: UUID
    ciphertext: bytes
    nonce: bytes
    tag: bytes
    wrapped_dek: bytes
    enc_alg: str | None = field(default="AES-256-GCM")
    wrap_alg: str | None = field(default="RSA-OAEP-256")
    encoding: str | None = field(default="utf8")

    def reveal(self, crypto_client: CryptoClient) -> str:
        return crypto_client.decrypt_secret(
            wrapped_dek=self.wrapped_dek,
            aad={
                "organization_id": self.organization_id,
                "user_id": self.user_id,
                "datastore_id": self.datastore_id,
            },
            nonce=self.nonce,
            ciphertext=self.ciphertext,
            tag=self.tag,
        )
