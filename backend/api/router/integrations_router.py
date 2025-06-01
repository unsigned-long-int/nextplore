from fastapi import APIRouter, Depends
from typing import List

from services.database.dependencies import backend_session_scope
from services.database.models import Organization, User, Integration
from services.authentication import get_active_user
from api.models import IntegrationProfile

router = APIRouter()

@router.get('', response_model=List[IntegrationProfile])
def get_integrations(
    user=Depends(get_active_user)
) ->  List[IntegrationProfile]:
    with backend_session_scope() as scoped_session:
        sub = user.get('sub')

        user = (
            scoped_session.query(User)
            .filter_by(sub=sub)
            .first()
        )
        org = (
            scoped_session.query(Organization)
            .filter_by(id=user.organization_id)
            .first()
        )

        integrations = (
            scoped_session.query(Integration)
            .filter_by(organization_id=org.id, user_id=user.id)
            )

        return [
            IntegrationProfile(
                id=integration.id,
                service_type=integration.service_type,
                connection_name=integration.connection_name,
                database_name=integration.database_name,
                auth_method=integration.auth_method
            )
            for integration in integrations
        ]