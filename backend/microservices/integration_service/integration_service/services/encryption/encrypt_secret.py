import json
from typing import Any, Dict
from uuid import UUID

from integration_service.domain.models.secret import DataStoreSecret
from nextplore_sdk.encryptor.client.crypto_client import CryptoClient
from nextplore_sdk.encryptor.client.encrypted_secret import EncryptedSecret


def encrypt_secret(
    organization_id: UUID,
    user_id: UUID,
    datastore_id: UUID,
    plaintext: str,
    crypto_client: CryptoClient,
    **kwargs: Any
) -> DataStoreSecret:
    encrypted_secret = crypto_client.encrypt_secret(
        plaintext=plaintext,
        aad={
            'organization_id': organization_id,
            'user_id': user_id,
            'datastore_id': datastore_id
        }
    )
    return DataStoreSecret(
        organization_id=organization_id,
        user_id=user_id,
        datastore_id=datastore_id,
        ciphertext=encrypted_secret.ciphertext,
        nonce=encrypted_secret.nonce,
        tag=encrypted_secret.tag,
        wrapped_dek=encrypted_secret.wrapped_dek,
        **kwargs
    )


def encrypt_conn_params(
    organization_id: UUID,
    user_id: UUID,
    api_base: str,
    model_id: str,
    crypto_client: CryptoClient,
    conn_params: Dict[str, Any],
) -> EncryptedSecret:
    encrypted_conn_params = crypto_client.encrypt_secret(
        plaintext=json.dumps(conn_params),
        aad={
            'organization_id': organization_id,
            'user_id': user_id,
            'api_base': api_base,
            'model_id': model_id,
        }
    )

    return encrypted_conn_params

