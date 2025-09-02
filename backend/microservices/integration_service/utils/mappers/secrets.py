from typing import List
from uuid import UUID

from domain_models import Secret
from nextplore_sdk.encryptor.secret_types import SECRET_TYPES
from nextplore_sdk.contracts.integration_service.prepared_integration_create_request import PreparedIntegrationCreateRequest
from nextplore_sdk.encryptor.encrypted_secret import EncryptedSecret
from nextplore_sdk.encryptor.crypto_client import CryptoClient

KEK_KID = 'https://nextplore-keyvault.vault.azure.net/keys/kek-8f70164e-3b25-4e26-9938-bea8c8bd314d/4a06015fb28b4765976f7ab806ad4708'


def to_domain_secrets(
        organization_id: UUID,
        user_id: UUID,
        integration_id: UUID,
        integration_create_request: PreparedIntegrationCreateRequest
) -> List[Secret]:
    secrets: List[Secret]

    crypto_client = CryptoClient(KEK_KID)
    for name, val in integration_create_request.model_dump(exclude_none=True).items():
        if name not in SECRET_TYPES:
            continue
        
        encrypted_secret: EncryptedSecret = crypto_client.encrypt_secret(val)
        secret = Secret(
            organization_id=organization_id,
            user_id=user_id,
            integration_id=integration_id,
            secret_type=name,
            ciphertext=encrypted_secret.ciphertext,
            nonce=encrypted_secret.nonce,
            tag=encrypted_secret.tag,
            wrapped_dek=encrypted_secret.wrapped_dek,
            kek_kid=crypto_client.kek_kid,
            aad=encrypted_secret.aad
        )
        secrets.append(secret)
    return secrets