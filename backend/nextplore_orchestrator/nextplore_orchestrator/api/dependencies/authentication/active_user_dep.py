from fastapi import Depends
from nextplore_sdk.database.backend.database_backend_connector import (
    DatabaseBackendConnector,
)

from nextplore_orchestrator.api.context import UserIdentity, set_current_identity
from nextplore_orchestrator.api.dependencies.cache import get_identity_cache_service
from nextplore_orchestrator.api.dependencies.connector import get_backend_connector
from nextplore_orchestrator.cache.identity_cache import IdentityCacheService
from nextplore_orchestrator.services.identity import resolve_user_identity

from .azure_user_dep import get_azure_user


async def get_active_user(
    azure_user=Depends(get_azure_user),
    identity_cache_service: IdentityCacheService = Depends(get_identity_cache_service),
    backend_connector: DatabaseBackendConnector = Depends(get_backend_connector),
) -> UserIdentity:
    azure_tenant_id = azure_user.get("tid")
    azure_user_id = azure_user.get("oid")
    cached = await identity_cache_service.get_user_identity(
        azure_tenant_id, azure_user_id
    )
    if cached:
        set_current_identity(cached)
        return cached

    identity = await resolve_user_identity(
        azure_tenant_id=azure_tenant_id,
        azure_user_id=azure_user_id,
        backend_connector=backend_connector,
    )

    await identity_cache_service.set_user_identity(
        tid=azure_tenant_id, oid=azure_user_id, identity=identity
    )

    set_current_identity(identity)
    return identity
