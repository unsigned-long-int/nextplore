from uuid import UUID
from typing import Dict, Any, List
from pydantic import SecretStr

from integration_service.database.models import SecretORM
from integration_service.services.encryption import encrypt_secret
from nextplore_sdk.encryptor.client.crypto_client import CryptoClient
from integration_service.domain.models.secret import IntegrationSecret, SecretType
from integration_service.api.models.integration_update_request import IntegrationUpdateRequest
from integration_service.api.models.integration_create_request import IntegrationCreateRequest


def secrets_from_dto(
    organization_id: UUID,
    user_id: UUID,
    integration_id: UUID,
    crypto_client: CryptoClient,
    payload: IntegrationUpdateRequest | IntegrationCreateRequest,
    **kwargs: Any
) -> Dict[SecretType, IntegrationSecret]:
    secrets: Dict[SecretType, IntegrationSecret] = {}

    for name, val in payload.model_dump().items():
        if not isinstance(val, SecretStr):
            continue

        encrypted_secret = encrypt_secret(
            organization_id=organization_id,
            user_id=user_id,
            integration_id=integration_id,
            plaintext=val.get_secret_value(),
            crypto_client=crypto_client,
            **kwargs
        )
        secrets.update({name: encrypted_secret})
    return secrets


def secrets_from_orm(secrets_orm: List[SecretORM]) -> Dict[SecretType, IntegrationSecret]:
    return {
        s.secret_type: IntegrationSecret(
                organization_id=s.organization_id,
                user_id=s.user_id,
                integration_id=s.integration_id,
                ciphertext=s.ciphertext,
                nonce=s.nonce,
                tag=s.tag,
                wrapped_dek=s.wrapped_dek,
                enc_alg=s.enc_alg,
                wrap_alg=s.wrap_alg,
                encoding=s.encoding
            )
        for s in secrets_orm
    }


def orm_from_secrets(secrets: Dict[SecretType, IntegrationSecret]) -> List[SecretORM]:
    return [
        SecretORM(
            organization_id=secret.organization_id,
            user_id=secret.user_id,
            integration_id=secret.integration_id,
            secret_type=secret_type,
            ciphertext=secret.ciphertext,
            nonce=secret.nonce,
            tag=secret.tag,
            wrapped_dek=secret.wrapped_dek,
            enc_alg=secret.enc_alg,
            wrap_alg=secret.wrap_alg,
            encoding=secret.encoding,
            version=secret.version
        )
        for secret_type, secret in secrets.items()
    ]
