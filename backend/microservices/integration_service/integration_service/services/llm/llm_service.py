import logging
from typing import Callable, List

from integration_service.api.context import UserIdentity
from integration_service.cache import CacheService
from integration_service.database.exceptions import UserLlmCreateFailed, UserLlmGetFailed
from integration_service.database.repositories import LlmRepository
from integration_service.domain.mappers.user_llm.converter import user_llm_from_dto
from integration_service.domain.models.user_llm import UserLlmProfile

from svc_integration_contracts.models import UserLlmCreateRequest
from nextplore_sdk.encryptor.client.crypto_client import CryptoClient


logger = logging.getLogger(__name__)


class LlmService:
    def __init__(
        self,
        repo: LlmRepository,
        cache_service: CacheService,
        crypto_client_factory: Callable[[str], CryptoClient]
    ) -> None:
        self._repo = repo
        self._cache_service = cache_service
        self._crypto_client_factory = crypto_client_factory


    async def create_user_llm(
        self,
        user_identity: UserIdentity,
        payload: UserLlmCreateRequest
    ) -> None:
        model_id = None
        try:
            crypto_client = self._crypto_client_factory(payload.kek_kid)
            user_llm = user_llm_from_dto(
                organization_id=user_identity.organization_id,
                user_id=user_identity.user_id,
                payload=payload,
                crypto_client=crypto_client
            )
            model_id =  await self._repo.create_user_llm(
                organization_id=user_identity.organization_id,
                user_id=user_identity.user_id,
                user_llm=user_llm
            )
            await self._cache_service.delete_user_llm_profiles(user_identity)
        except UserLlmCreateFailed as e:
            logger.error(
                'Create user llm failed due to database dependency.',
                extra={
                    'organization_id': user_identity.organization_id,
                    'user_id': user_identity.user_id,
                    'model_id': str(model_id) if model_id else None,
                    'error_type': type(e).__name__,
                },
                exc_info=True
            )
            raise
        except Exception as e:
            logger.error(
                'Unexpected error during user llm creation.',
                extra={
                    'org_id': str(user_identity.organization_id),
                    'user_id': str(user_identity.user_id),
                    'model_id': str(model_id) if model_id else None,
                    'error_type': type(e).__name__,
                },
                exc_info=True,
            )
            raise

    async def get_user_llm_profiles(
        self,
        user_identity: UserIdentity,
    ) -> List[UserLlmProfile]:
        try:
            cached = await self._cache_service.get_user_llm_profiles(user_identity)
            if cached:
                return cached

            user_llm_profiles = await self._repo.get_user_llm_profiles(
                organization_id=user_identity.organization_id,
                user_id=user_identity.user_id,
            )
            await self._cache_service.set_user_llm_profiles(user_identity, user_llm_profiles)
            return user_llm_profiles
        except UserLlmGetFailed as e:
            logger.error(
                'Get user llm profiles failed due to database dependency.',
                extra={'organization_id': user_identity.organization_id,
                    'user_id': user_identity.user_id,
                    'error_type': type(e).__name__,
                },
                exc_info=True
            )
            raise
        except Exception as e:
            logger.error(
                'Unexpected error during user llm retrieval.',
                extra={
                    'org_id': str(user_identity.organization_id),
                    'user_id': str(user_identity.user_id),
                    'error_type': type(e).__name__,
                },
                exc_info=True,
            )
            raise
