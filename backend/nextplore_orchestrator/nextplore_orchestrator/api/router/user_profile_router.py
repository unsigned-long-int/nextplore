import os
from fastapi import APIRouter, Depends

from nextplore_sdk.database.backend.database_backend_connector import DatabaseBackendConnector
from nextplore_sdk.encryptor.provider.azure_vault_key_provider import AzureVaultKeyProvider
from nextplore_orchestrator.api.models.user_profile import UserProfile
from nextplore_orchestrator.cache.orchestrator_cache import OrchestratorCacheService
from nextplore_orchestrator.database.repositories import AuthRepository
from nextplore_orchestrator.domain.mappers import user_from_dto, organization_from_dto
from nextplore_orchestrator.api.dependencies.cache import get_orchestrator_cache_service
from nextplore_orchestrator.api.dependencies.authentication import get_azure_user
from nextplore_orchestrator.api.dependencies.connector import get_backend_connector


router = APIRouter(prefix='/v1/nextplore-orchestrator', tags=['UserProfile'])


@router.get('/users/profiles', response_model=UserProfile)
async def get_user_profile(
    user=Depends(get_azure_user),
    backend_connector: DatabaseBackendConnector = Depends(get_backend_connector),
    cache_service: OrchestratorCacheService = Depends(get_orchestrator_cache_service)
) -> UserProfile:
    email = user.get('preferred_username')
    if not email:
        raise ValueError('preferred_username claim is missing')
    
    azure_tenant_id = user.get('tid')
    azure_user_id = user.get('oid')

    cached = await cache_service.get_user_profile(
        azure_tenant_id,
        azure_user_id
    )
    if cached:
        return cached

    auth_repo = AuthRepository(backend_connector)

    organization_id = await auth_repo.get_org(azure_tenant_id)
    org = organization_from_dto(user)
    if not organization_id:
        key_vault_provider = AzureVaultKeyProvider(key_vault_url=os.getenv('VAULT_URL'))
        kek_kid = key_vault_provider.create_vault(azure_tenant_id)
        organization_id = await auth_repo.create_org(organization=org, kek_kid=kek_kid)

    usr = user_from_dto(user, organization_id)
    user_id = await auth_repo.get_user(usr)
    if not user_id:
        user_id = await auth_repo.create_user(usr)

    response = UserProfile(
        id=user_id,
        email=usr.email,
        name=usr.name,
        organization=org.name,
        organization_id=organization_id
    )

    await cache_service.set_user_profile(
        org.azure_tenant_id,
        usr.azure_user_id,
        response=response,
        ttl=300
    )

    return response
