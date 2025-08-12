from fastapi import Depends

from nextplore_sdk.identity_service.identity_model.user_identity import UserIdentity
from nextplore_sdk.identity_service.resolver.resolve_user_identity import resolve_user_identity
from api.dependencies.cache import get_identity_cache_service
from api.context import set_current_identity
from cache.identity_cache import IdentityCacheService
from .azure_user_dep import get_azure_user


async def get_active_user(
    azure_user = Depends(get_azure_user),
    identity_cache_service: IdentityCacheService = Depends(get_identity_cache_service)
) -> UserIdentity:
    azure_tenant_id = azure_user.get('tid')
    azure_user_id = azure_user.get('oid')
    cached = await identity_cache_service.get_user_identity(azure_tenant_id, azure_user_id)
    if cached:
        set_current_identity(cached)
        return cached
    
    identity = await resolve_user_identity(azure_tenant_id, azure_user_id)

    await identity_cache_service.set_user_identity(
        tid=azure_tenant_id,
        oid=azure_user_id,
        identity=identity
    )

    set_current_identity(identity)
    return identity
