from typing import Any
from uuid import UUID

from nextplore_sdk.encryptor.client.crypto_client import CryptoClient

from integration_service.domain.models.secret import DataStoreSecret, SecretType
from integration_service.domain.models.user_llm import UserLlm


def decrypt_secret(
    secret_type: SecretType,
    secrets: dict[SecretType, DataStoreSecret],
    crypto_client: CryptoClient,
) -> str | None:
    if secrets.get(secret_type) is None:
        return None
    return secrets.get(secret_type).reveal(crypto_client)


def decrypt_conn_params(
    crypto_client: CryptoClient, organization_id: UUID, user_id: UUID, user_llm: UserLlm
) -> dict[str, Any]:
    return user_llm.reveal(
        crypto_client=crypto_client, organization_id=organization_id, user_id=user_id
    )
