from typing import List
from uuid import UUID

from services.database.models import IntegrationORM
from services.identity_service import UserIdentity
from services.database.dependencies import backend_session_scope


class IntegrationRepository:
    def get_user_integration_ids(self, user_identity: UserIdentity) -> List[UUID]:
        with backend_session_scope() as scoped_session:
            integrations_orm = (
                scoped_session.query(IntegrationORM)
                .filter_by(organization_id=user_identity.organization_id, user_id=user_identity.user_id)
                .all()
            )
            return [integration_orm.id for integration_orm in integrations_orm]
        