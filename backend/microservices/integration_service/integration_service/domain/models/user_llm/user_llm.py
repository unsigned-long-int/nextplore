import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from nextplore_sdk.encryptor.client.crypto_client import CryptoClient
from nextplore_sdk.encryptor.client.encrypted_secret import EncryptedSecret


@dataclass(frozen=True)
class UserLlm:
    model_id: str
    label: str
    kek_kid: str
    api_base: str
    nonce: bytes
    encrypted_conn_params: EncryptedSecret
    max_tokens: int = 4096

    def reveal(
        self, crypto_client: CryptoClient, organization_id: UUID, user_id: UUID
    ) -> dict[str, Any]:
        decrypted = crypto_client.decrypt_secret(
            wrapped_dek=self.encrypted_conn_params.wrapped_dek,
            aad={
                "organization_id": organization_id,
                "user_id": user_id,
                "api_base": self.api_base,
                "model_id": self.model_id,
            },
            nonce=self.nonce,
            ciphertext=self.encrypted_conn_params.ciphertext,
            tag=self.encrypted_conn_params.tag,
        )
        return json.loads(decrypted)
