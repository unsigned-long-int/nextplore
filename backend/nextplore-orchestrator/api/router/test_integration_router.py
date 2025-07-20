from fastapi import APIRouter, Depends
from httpx import HTTPStatusError

from api.dependencies.authentication import get_active_user
from api.dependencies.microservices import get_integration_client
from shared.contracts.integration_service import PreparedIntegrationTestRequest
from api.models import IntegrationCreateRequest, IntegrationTestResponse


router = APIRouter()

@router.post('')
async def test_integration(
    integration_create_request: IntegrationCreateRequest,
    user_identity=Depends(get_active_user),
    integration_client=Depends(get_integration_client)
) -> IntegrationTestResponse:
    payload = PreparedIntegrationTestRequest(
        service_type=integration_create_request.service_type,
        auth_method=integration_create_request.auth_method,
        connection_name=integration_create_request.connection_name,
        host=integration_create_request.host,
        port=integration_create_request.port,
        database_name=integration_create_request.database_name,
        username=integration_create_request.username,
        password=integration_create_request.password,
        kerberos_principal=integration_create_request.kerberos_principal,
        windows_domain=integration_create_request.windows_domain,
        extra_options=integration_create_request.extra_options,
        autosync_on=integration_create_request.autosync_on
    )

    try:
        await integration_client.test_integration(payload)
        return IntegrationTestResponse(success=True)
    except HTTPStatusError as e:
        return IntegrationTestResponse(success=False, message=str(e))

