import logging
from fastapi import APIRouter, Depends, HTTPException, Response, status

from nextplore_sdk.database.backend.database_backend_connector import DatabaseBackendConnector
from nextplore_orchestrator.clients.integration.models.integration_create_request import IntegrationCreateRequest
from nextplore_orchestrator.api.dependencies.authentication import get_active_user
from nextplore_orchestrator.api.dependencies.microservices import get_integration_client
from nextplore_orchestrator.api.dependencies.connector import get_backend_connector
from nextplore_orchestrator.database.repositories import AuthRepository
from nextplore_orchestrator.database.exceptions import KekIdNotFound, KekIdGetFailed
from nextplore_orchestrator.clients.integration import IntegrationCreateRemoteError


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/nextplore-orchestrator', tags=['CreateIntegration'])


@router.post('/integrations', status_code=status.HTTP_201_CREATED)
async def create_integration(
    integration_create_request: IntegrationCreateRequest,
    user_identity=Depends(get_active_user),
    backend_connector: DatabaseBackendConnector = Depends(get_backend_connector),
    integration_client=Depends(get_integration_client)
) -> Response:
    org_id = getattr(user_identity, 'organization_id', None)
    user_id = getattr(user_identity, 'user_id', None)

    auth_repo = AuthRepository(backend_connector)

    try:
        kek_kid = await auth_repo.get_kek_kid(org_id)
        enriched_integration = integration_create_request.copy(update={'kek_kid': kek_kid})
        await integration_client.create_integration(
            organization_id=org_id,
            user_id=user_id,
            payload=enriched_integration
        )
        return Response(status_code=status.HTTP_201_CREATED)
    except IntegrationCreateRemoteError as e:
        logger.error(
            'Create integration failed (remote)',
            extra={'org_id': org_id, 'user_id': user_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )
    except (KekIdGetFailed, KekIdNotFound) as e:
        logger.error(
            'Create integration failed (Kek ID not found)',
            extra={'org_id': org_id, 'user_id': user_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )
    except Exception as e:
        logger.error(
            'Create integration failed (unexpected)',
            extra={'org_id': org_id, 'user_id': user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
