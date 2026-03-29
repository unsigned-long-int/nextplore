import logging
from fastapi import APIRouter, Depends, HTTPException, status

from nextplore_orchestrator.clients.integration import DataStoreTestRemoteError
from nextplore_orchestrator.api.dependencies.authentication import get_active_user
from nextplore_orchestrator.api.dependencies.microservices import get_integration_client
from nextplore_orchestrator.api.models.integration_test_response import IntegrationTestResponse

from svc_integration_contracts.models import DataStoreCreateRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/nextplore-orchestrator', tags=['DataStore'])


@router.post('/datastores/test')
async def test_datastore(
    datastore_create_request: DataStoreCreateRequest,
    user_identity=Depends(get_active_user),
    integration_client=Depends(get_integration_client)
) -> DataStoreTestResponse:
    org_id = getattr(user_identity, 'organization_id', None)
    user_id = getattr(user_identity, 'user_id', None)
    
    try:
        await integration_client.test_integration(datastore_create_request)
        return IntegrationTestResponse(success=True)
    except DataStoreTestRemoteError as e:
        logger.error(
            'Data store test failed (remote)',
            extra={'org_id': str(org_id), 'user_id': str(user_id)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )
    except Exception as e:
        logger.error(
            'Data store test failed (unexpected)',
            extra={'org_id': str(org_id), 'user_id': str(user_id)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )

