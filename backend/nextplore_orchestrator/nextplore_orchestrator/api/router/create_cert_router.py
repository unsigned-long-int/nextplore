import logging
from fastapi import APIRouter, Depends, HTTPException, Response, status

from nextplore_orchestrator.api.dependencies.authentication import get_active_user
from nextplore_orchestrator.api.dependencies.microservices import get_integration_client
from nextplore_orchestrator.clients.integration import CertCreateRemoteError
from nextplore_orchestrator.clients.integration.models.cert_create_request import CertCreateRequest


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/nextplore-orchestrator', tags=['CreateCertificate'])


@router.post('/datastores/certificates', status_code=status.HTTP_201_CREATED)
async def create_certificate(
    cert_create_request: CertCreateRequest,
    user_identity=Depends(get_active_user),
    integration_client=Depends(get_integration_client)
) -> Response:
    org_id = getattr(user_identity, 'organization_id', None)
    user_id = getattr(user_identity, 'user_id', None)

    try:
        await integration_client.create_cert(
            organization_id=org_id,
            user_id=user_id,
            payload=cert_create_request
        )
        return Response(status_code=status.HTTP_201_CREATED)
    except CertCreateRemoteError as e:
        logger.error(
            'Create certificate failed (remote)',
            extra={'org_id': org_id, 'user_id': user_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )
    except Exception as e:
        logger.error(
            'Create certificate failed (unexpected)',
            extra={'org_id': org_id, 'user_id': user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
