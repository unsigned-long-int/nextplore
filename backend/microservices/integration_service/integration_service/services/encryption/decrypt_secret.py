from typing import Optional, Dict

from integration_service.domain.models.secret import SecretType, IntegrationSecret
from nextplore_sdk.encryptor.client.crypto_client import CryptoClient


def decrypt_secret(
    secret_type: SecretType,
    secrets: Dict[SecretType, IntegrationSecret],
    crypto_client: CryptoClient
) -> Optional[str]:
    if secrets.get(secret_type) is None:
        return None
    return secrets.get(secret_type).reveal(crypto_client)
