from sqlalchemy import select

from nextplore_sdk.database.models.user_orm import UserORM
from nextplore_sdk.database.models.organization_orm import OrganizationORM
from nextplore_sdk.database.dependencies.database_backend_connector import DatabaseBackendConnector
from nextplore_sdk.identity_service.identity_model.user_identity import UserIdentity


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

    identity = UserIdentity(
            organization_id=org.id,
            user_id=user.id
    )
    return identity