from sqlalchemy import select

from shared.database.models import (
    UserORM, 
    OrganizationORM
)
from shared.database.dependencies import DatabaseBackendConnector
from shared.identity_service.user_identity import UserIdentity


async def resolve_user_identity(azure_tenant_id: str, azure_user_id: str) -> UserIdentity:
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

        return UserIdentity(
            organization_id=org.id,
            user_id=user.id
        )