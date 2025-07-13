from shared.database.models import (
    UserORM, 
    OrganizationORM
)
from shared.database.dependencies import backend_session_scope
from .user_identity import UserIdentity


def resolve_user_identity(azure_tenant_id: str, azure_user_id: str) -> UserIdentity:
    with backend_session_scope() as scoped_session:
        org = (
            scoped_session.query(OrganizationORM)
            .filter_by(azure_tenant_id=azure_tenant_id)
            .first()
        )
        user = (
            scoped_session.query(UserORM)
            .filter_by(azure_user_id=azure_user_id, organization_id=org.id)
            .first()
        )

        return UserIdentity(
            organization_id=org.id,
            user_id=user.id
        )