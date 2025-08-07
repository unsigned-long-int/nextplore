from fastapi import APIRouter, status, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from api.context import get_current_identity
from messaging.message_bus import get_kafka_message_bus
from messaging.events.integration_service import IntegrationDeleted
from database.repositories import IntegrationRepository, IntegrationDeleteFailed
from nextplore_shared.cache.service_caches.integration_cache.cache import integration_service_cache
from nextplore_shared.contracts.integration_service.prepared_integration_delete_request import PreparedIntegrationDeleteRequest


router = APIRouter(prefix='/v1/integration', tags=['Integration'])

@router.post('/delete-integration', status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(payload: PreparedIntegrationDeleteRequest) -> JSONResponse:
    user_identity = get_current_identity()
    integration_repo = IntegrationRepository()
    try:
        await integration_repo.delete_integration(
            integration_id=payload.integration_id,
            user_id=payload.user_id, 
            organization_id=payload.organization_id
        )
        await get_kafka_message_bus().publish(
            IntegrationDeleted(
                user_id=user_identity.user_id,
                organization_id=user_identity.organization_id,
                integration_id=payload.integration_id
            )
        )
        await integration_service_cache.delete_by_prefix(
            user_identity.organization_id,
            user_identity.user_id
        )

    except IntegrationDeleteFailed as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Database error: {str(e)}'
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Unhandled error: {str(e)}'
        )
