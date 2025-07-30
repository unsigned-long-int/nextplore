from fastapi import APIRouter, status, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from database.repositories import IntegrationRepository, IntegrationDeleteFailed
from shared.contracts.integration_service import PreparedIntegrationDeleteRequest


router = APIRouter(prefix='/v1/integration', tags=['Integration'])

@router.post('/delete-integration', status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(payload: PreparedIntegrationDeleteRequest) -> JSONResponse:
    integration_repo = IntegrationRepository()
    try:
        await integration_repo.delete_integration(
            integration_id=payload.integration_id,
            user_id=payload.user_id, 
            organization_id=payload.organization_id
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
