from fastapi import APIRouter, Depends
from typing import List

from shared.database.dependencies import backend_session_scope
from shared.database.models import IntegrationORM
from internal_services.authentication import get_active_user
from shared.identity_service import resolve_user_identity
from api.models import IntegrationProfile

router = APIRouter()

@router.get('', response_model=List[IntegrationProfile])
def get_integrations(user=Depends(get_active_user)) ->  List[IntegrationProfile]:
    azure_user_id = user.get('oid')
    azure_tenant_id = user.get('tid')

    user_identity = resolve_user_identity(azure_tenant_id, azure_user_id)
    with backend_session_scope() as scoped_session:
        integrations_orm = (
            scoped_session.query(IntegrationORM)
            .filter_by(organization_id=user_identity.organization_id, user_id=user_identity.user_id)
        )

        return [
            IntegrationProfile(
                id=integration.id,
                service_type=integration.service_type,
                connection_name=integration.connection_name,
                database_name=integration.database_name,
                auth_method=integration.auth_method,
                autosync_on=integration.autosync_on
            )
            for integration in integrations_orm
        ]