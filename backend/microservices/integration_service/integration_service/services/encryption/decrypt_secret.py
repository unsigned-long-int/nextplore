from typing import Optional, Dict, Any
from uuid import UUID

from integration_service.domain.models.secret import SecretType, DataStoreSecret
from integration_service.domain.models.user_llm import UserLlm

from nextplore_sdk.encryptor.client.crypto_client import CryptoClient


def decrypt_secret(
    secret_type: SecretType,
    secrets: Dict[SecretType, DataStoreSecret],
    crypto_client: CryptoClient
) -> Optional[str]:
    if secrets.get(secret_type) is None:
        return None
    return secrets.get(secret_type).reveal(crypto_client)

def decrypt_conn_params(
    crypto_client: CryptoClient,
    organization_id: UUID,
    user_id: UUID,
    user_llm: UserLlm
) -> Dict[str, Any]:
    return user_llm.reveal(
        crypto_client=crypto_client,
        organization_id=organization_id,
        user_id=user_id
    )