import logging
from typing import Any
from uuid import UUID

from nextplore_sdk.encryptor.client.crypto_client import CryptoClient
from pydantic import SecretStr
from svc_integration_contracts.models import (
    DataStoreCreateRequest,
    DataStoreUpdateRequest,
)

from integration_service.database.models import SecretORM
from integration_service.domain.models.secret import DataStoreSecret, SecretType
from integration_service.services.encryption import encrypt_secret

logger = logging.getLogger(__name__)


def secrets_from_dto(
    organization_id: UUID,
    user_id: UUID,
    datastore_id: UUID,
    crypto_client: CryptoClient,
    payload: DataStoreUpdateRequest | DataStoreCreateRequest,
    **kwargs: Any,
) -> dict[SecretType, DataStoreSecret]:
    secrets: dict[SecretType, DataStoreSecret] = {}

    for name, val in payload.model_dump().items():
        if not isinstance(val, SecretStr):
            continue
        try:
            secret_type = SecretType(name)
        except ValueError:
            logger.warning(f"Field {name} is a SecretStr but not a valid SecretType")
            continue

        encrypted_secret = encrypt_secret(
            organization_id=organization_id,
            user_id=user_id,
            datastore_id=datastore_id,
            plaintext=val.get_secret_value(),
            crypto_client=crypto_client,
            **kwargs,
        )
        secrets[secret_type] = encrypted_secret
    return secrets


def secrets_from_orm(secrets_orm: list[SecretORM]) -> dict[SecretType, DataStoreSecret]:
    return {
        s.secret_type: DataStoreSecret(
            organization_id=s.organization_id,
            user_id=s.user_id,
            datastore_id=s.datastore_id,
            ciphertext=s.ciphertext,
            nonce=s.nonce,
            tag=s.tag,
            wrapped_dek=s.wrapped_dek,
            enc_alg=s.enc_alg,
            wrap_alg=s.wrap_alg,
            encoding=s.encoding,
        )
        for s in secrets_orm
    }


def orm_from_secrets(
    secrets: dict[SecretType, DataStoreSecret], version: int = 1
) -> list[SecretORM]:
    return [
        SecretORM(
            organization_id=secret.organization_id,
            user_id=secret.user_id,
            datastore_id=secret.datastore_id,
            secret_type=secret_type,
            ciphertext=secret.ciphertext,
            nonce=secret.nonce,
            tag=secret.tag,
            wrapped_dek=secret.wrapped_dek,
            enc_alg=secret.enc_alg,
            wrap_alg=secret.wrap_alg,
            encoding=secret.encoding,
            version=version,
        )
        for secret_type, secret in secrets.items()
    ]
