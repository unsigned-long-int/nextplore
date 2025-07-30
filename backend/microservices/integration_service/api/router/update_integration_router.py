from fastapi import APIRouter, status, HTTPException
from sqlalchemy.exc import SQLAlchemyError


from database.repositories import (
    IntegrationRepository,
    IntegrationUpdateFailed
)
from shared.contracts.integration_service import PreparedIntegrationUpdateRequest


router = APIRouter(prefix='/v1/integration', tags=['Integration'])

@router.post('/update-integration', status_code=status.HTTP_204_NO_CONTENT)
async def update_integration(payload: PreparedIntegrationUpdateRequest) -> None:
    integration_repo = IntegrationRepository()
    try:
        await integration_repo.update_integration(
            integration_id=payload.integration_id,
            user_id=payload.user_id,
            organization_id=payload.organization_id,
            update_args=payload.update_args
        )
    
    except IntegrationUpdateFailed as e:
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
