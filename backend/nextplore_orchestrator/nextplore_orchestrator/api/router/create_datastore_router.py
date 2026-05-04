import logging
from fastapi import APIRouter, Depends, HTTPException, Response, status

from nextplore_orchestrator.api.dependencies.authentication import get_active_user
from nextplore_orchestrator.api.dependencies.microservices import get_integration_client
from nextplore_orchestrator.api.dependencies.connector import get_backend_connector
from nextplore_orchestrator.database.repositories import AuthRepository
from nextplore_orchestrator.database.exceptions import KekIdNotFound, KekIdGetFailed
from nextplore_orchestrator.clients.integration import DataStoreCreateRemoteError

from nextplore_sdk.database.backend.database_backend_connector import DatabaseBackendConnector
from svc_integration_contracts.models import DataStoreCreateRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/nextplore-orchestrator', tags=['CreateDataStore'])


@router.post('/datastores', status_code=status.HTTP_201_CREATED)
async def create_datastore(
    datastore_create_request: DataStoreCreateRequest,
    user_identity=Depends(get_active_user),
    backend_connector: DatabaseBackendConnector = Depends(get_backend_connector),
    integration_client=Depends(get_integration_client)
) -> Response:
    org_id = getattr(user_identity, 'organization_id', None)
    user_id = getattr(user_identity, 'user_id', None)

    try:
        async with backend_connector.session_scope() as scoped_session:
            auth_repo = AuthRepository(scoped_session)
            kek_kid = await auth_repo.get_kek_kid(org_id)
            enriched_datastore = datastore_create_request.model_copy(update={'kek_kid': kek_kid})
            await integration_client.create_datastore(
                organization_id=org_id,
                user_id=user_id,
                payload=enriched_datastore
            )
            return Response(status_code=status.HTTP_201_CREATED)
    except DataStoreCreateRemoteError as e:
        logger.error(
            'Create data store failed (remote)',
            extra={'org_id': org_id, 'user_id': user_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )
    except (KekIdGetFailed, KekIdNotFound) as e:
        logger.error(
            'Create data store failed (Kek ID not found)',
            extra={'org_id': org_id, 'user_id': user_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )
    except Exception as e:
        logger.error(
            'Create data store failed (unexpected)',
            extra={'org_id': org_id, 'user_id': user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
