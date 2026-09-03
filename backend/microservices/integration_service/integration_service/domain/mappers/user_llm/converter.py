from uuid import UUID

from nextplore_sdk.encryptor.client.crypto_client import CryptoClient
from nextplore_sdk.encryptor.client.encrypted_secret import EncryptedSecret
from svc_integration_contracts.models import UserLlmCreateRequest

from integration_service.database.models import UserLlmORM
from integration_service.domain.models.user_llm import UserLlm, UserLlmProfile
from integration_service.services.encryption import encrypt_conn_params


def orm_from_user_llm(
    organization_id: UUID, user_id: UUID, user_llm: UserLlm
) -> UserLlmORM:
    return UserLlmORM(
        organization_id=organization_id,
        user_id=user_id,
        api_base=user_llm.api_base,
        label=user_llm.label,
        model_id=user_llm.model_id,
        max_tokens=user_llm.max_tokens,
        encrypted_connection_params=user_llm.encrypted_conn_params.ciphertext,
        nonce=user_llm.encrypted_conn_params.nonce,
        tag=user_llm.encrypted_conn_params.tag,
        wrapped_dek=user_llm.encrypted_conn_params.wrapped_dek,
        kek_kid=user_llm.kek_kid,
    )


def user_llm_from_orm(
    organization_id: UUID, user_id: UUID, user_llm_orm: UserLlmORM
) -> UserLlm:
    encrypted_secret = EncryptedSecret(
        nonce=user_llm_orm.nonce,
        tag=user_llm_orm.tag,
        aad={
            "organization_id": organization_id,
            "user_id": user_id,
            "api_base": user_llm_orm.api_base,
            "model_id": user_llm_orm.model_id,
        },
        ciphertext=user_llm_orm.encrypted_connection_params,
        wrapped_dek=user_llm_orm.wrapped_dek,
    )

    return UserLlm(
        model_id=user_llm_orm.model_id,
        label=user_llm_orm.label,
        kek_kid=user_llm_orm.kek_kid,
        api_base=user_llm_orm.api_base,
        nonce=user_llm_orm.nonce,
        encrypted_conn_params=encrypted_secret,
        max_tokens=user_llm_orm.max_tokens,
    )


def user_llm_from_dto(
    organization_id: UUID,
    user_id: UUID,
    payload: UserLlmCreateRequest,
    crypto_client: CryptoClient,
) -> UserLlm:
    encrypted_conn_params = encrypt_conn_params(
        organization_id=organization_id,
        user_id=user_id,
        model_id=payload.model_id,
        api_base=payload.api_base,
        crypto_client=crypto_client,
        conn_params=payload.connection_params,
    )
    return UserLlm(
        model_id=payload.model_id,
        label=payload.label,
        api_base=payload.api_base,
        nonce=encrypted_conn_params.nonce,
        encrypted_conn_params=encrypted_conn_params,
        max_tokens=payload.max_tokens,
        kek_kid=payload.kek_kid,
    )


def user_llm_profile_from_orm(user_llm_orm: UserLlmORM) -> UserLlmProfile:
    return UserLlmProfile(
        api_base=user_llm_orm.api_base,
        model_id=user_llm_orm.model_id,
        label=user_llm_orm.label,
        max_tokens=user_llm_orm.max_tokens,
        model_ref_id=user_llm_orm.id,
    )
