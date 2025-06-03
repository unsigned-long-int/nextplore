import uuid
import json
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from services.encryption import encrypt_secret
from services.database.dependencies import backend_session_scope
from services.database.models import User, Integration
from services.authentication import get_active_user
from api.models import IntegrationCreateRequest


router = APIRouter()

@router.post('')
def create_integration(
    integration_create_request: IntegrationCreateRequest,
    user=Depends(get_active_user)
    ):
    with backend_session_scope() as scoped_session:
        sub = user.get('sub')

        user = (
            scoped_session.query(User)
            .filter_by(sub=sub)
            .first()
        )

        integration = Integration(
            id = uuid.uuid4(),
            organization_id = user.organization_id,
            user_id = user.id,
            service_type = integration_create_request.service_type,
            auth_method = integration_create_request.auth_method,
            connection_name = integration_create_request.connection_name,
            host = integration_create_request.host,
            port = integration_create_request.port,
            database_name = integration_create_request.database_name,
            encrypted_username = encrypt_secret(integration_create_request.username) if integration_create_request.username else None,
            encrypted_password = encrypt_secret(integration_create_request.password) if integration_create_request.password else None,
            encrypted_kerberos_principal = encrypt_secret(integration_create_request.kerberos_principal) if integration_create_request.kerberos_principal else None,
            encrypted_windows_domain = encrypt_secret(integration_create_request.windows_domain) if integration_create_request.windows_domain else None,
            encrypted_extra_options = encrypt_secret(json.dumps(integration_create_request.extra_options)) if integration_create_request.extra_options else None
        )
        scoped_session.add(integration)
        scoped_session.flush()

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                'id': str(integration.id), 
                'connection_name': integration.connection_name
                }
            )