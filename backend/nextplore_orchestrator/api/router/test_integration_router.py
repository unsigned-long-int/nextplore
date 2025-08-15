import logging
from fastapi import APIRouter, Depends, HTTPException, status

from clients.integration import IntegrationTestRemoteError
from api.dependencies.authentication import get_active_user
from api.dependencies.microservices import get_integration_client
from nextplore_sdk.contracts.integration_service.prepared_integration_test_request import PreparedIntegrationTestRequest
from nextplore_sdk.contracts.nextplore_orchestrator_service.integration_create_request import IntegrationCreateRequest
from nextplore_sdk.contracts.nextplore_orchestrator_service.integration_test_response import IntegrationTestResponse


logger = logging.getLogger(__name__)

router = APIRouter()

@router.post('')
async def test_integration(
    integration_create_request: IntegrationCreateRequest,
    user_identity=Depends(get_active_user),
    integration_client=Depends(get_integration_client)
) -> IntegrationTestResponse:
    org_id = getattr(user_identity, 'organization_id', None)
    user_id = getattr(user_identity, 'user_id', None)

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
    except IntegrationTestRemoteError as e:
        logger.error(
            'Integration test failed (remote)',
            extra={'org_id': str(org_id), 'user_id': str(user_id)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )
    except Exception as e:
        logger.error(
            'Integration test failed (unexpected)',
            extra={'org_id': str(org_id), 'user_id': str(user_id)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )

