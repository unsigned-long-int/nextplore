from typing import Any
from uuid import UUID

from integration_service.domain.models.secret import IntegrationSecret
from nextplore_sdk.encryptor.client.crypto_client import CryptoClient


def encrypt_secret(
    organization_id: UUID,
    user_id: UUID,
    integration_id: UUID,
    plaintext: str,
    crypto_client: CryptoClient,
    **kwargs: Any
) -> IntegrationSecret:
    encrypted_secret = crypto_client.encrypt_secret(
        plaintext=plaintext,
        aad={
            'organization_id': organization_id,
            'user_id': user_id,
            'integration_id': integration_id
        }
    )
    return IntegrationSecret(
        organization_id=organization_id,
        user_id=user_id,
        integration_id=integration_id,
        ciphertext=encrypted_secret.ciphertext,
        nonce=encrypted_secret.nonce,
        tag=encrypted_secret.tag,
        wrapped_dek=encrypted_secret.wrapped_dek,
        **kwargs
    )
