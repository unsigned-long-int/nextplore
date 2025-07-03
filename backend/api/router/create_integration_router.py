import uuid
import json
from fastapi import APIRouter, Depends, status, BackgroundTasks
from fastapi.responses import JSONResponse

from services.encryption import encrypt_secret
from services.database.dependencies import backend_session_scope
from services.database.models import IntegrationORM
from services.authentication import get_active_user
from services.identity_service import resolve_user_identity
from api.models import IntegrationCreateRequest
from core.database.vectors_upsert import upsert_metadata


router = APIRouter()

@router.post('')
def create_integration(
    integration_create_request: IntegrationCreateRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_active_user)
) -> None:
    azure_user_id = user.get('oid')
    azure_tenant_id = user.get('tid')

    user_identity = resolve_user_identity(azure_tenant_id, azure_user_id)

    with backend_session_scope() as scoped_session:
        integration_orm = IntegrationORM(
            organization_id = user_identity.organization_id,
            user_id = user_identity.user_id,
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
        scoped_session.add(integration_orm)
        scoped_session.flush()

        connection_name = integration_orm.connection_name
        integration_id = integration_orm.id


    background_tasks.add_task(upsert_metadata, integration_id)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            'id': str(integration_id), 
            'connection_name': connection_name
            }
        )