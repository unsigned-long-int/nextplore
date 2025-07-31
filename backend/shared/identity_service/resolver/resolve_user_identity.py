from sqlalchemy import select

from shared.database.models import (
    UserORM, 
    OrganizationORM
)
from shared.database.dependencies import DatabaseBackendConnector
from shared.identity_service.user_identity import UserIdentity
from shared.cache.identity_cache import identity_cache_service


async def resolve_user_identity(azure_tenant_id: str, azure_user_id: str) -> UserIdentity:
    cached = await identity_cache_service.get_user_identity(azure_tenant_id, azure_user_id)
    if cached:
        return cached
    
    database_backend_connector = DatabaseBackendConnector()
    async with database_backend_connector.session_scope() as scoped_session:
        result = await scoped_session.execute(
            select(OrganizationORM)
            .where(OrganizationORM.azure_tenant_id == azure_tenant_id)
        )
        org = result.scalar_one_or_none()

        result = await scoped_session.execute(
            select(UserORM)
            .where(UserORM.azure_user_id == azure_user_id)
            .where(UserORM.organization_id == org.id)
        )
        user = result.scalar_one_or_none()

    identity = UserIdentity(
            organization_id=org.id,
            user_id=user.id
    )
    await identity_cache_service.set_user_identity(
        tid=azure_tenant_id,
        oid=azure_user_id,
        identity=identity
    )
    return identity