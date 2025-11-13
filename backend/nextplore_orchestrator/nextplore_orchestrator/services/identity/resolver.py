from sqlalchemy import select
from fastapi import HTTPException, status

from nextplore_orchestrator.api.context import UserIdentity
from nextplore_orchestrator.database.models import UserORM
from nextplore_orchestrator.database.models import OrganizationORM
from nextplore_sdk.database.backend.database_backend_connector import DatabaseBackendConnector


async def resolve_user_identity(
    azure_tenant_id: str,
    azure_user_id: str,
    backend_connector: DatabaseBackendConnector
) -> UserIdentity:
    async with backend_connector.session_scope() as scoped_session:
        result = await scoped_session.execute(
            select(OrganizationORM)
            .where(OrganizationORM.azure_tenant_id == azure_tenant_id)
        )
        org = result.scalar_one_or_none()
        if org is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={'message': f'Organization: {azure_tenant_id} is not registered'}
            )

        result = await scoped_session.execute(
            select(UserORM)
            .where(UserORM.azure_user_id == azure_user_id)
            .where(UserORM.organization_id == org.id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={'message': f'User: {azure_user_id} is not enrolled in organization: {org.id}'}
            )
    identity = UserIdentity(
            organization_id=org.id,
            user_id=user.id
    )
    return identity
