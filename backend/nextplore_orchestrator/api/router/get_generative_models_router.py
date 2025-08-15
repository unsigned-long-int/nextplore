import logging
from fastapi import APIRouter, Depends, HTTPException, status

from nextplore_sdk.contracts.ai_orm_context_service.avilable_models_response import AvailableModelsResponse
from clients.ai_orm_context import ModelResponseRemoteError
from api.dependencies.authentication import get_active_user
from api.dependencies.microservices import get_ai_orm_context_client


logger = logging.getLogger(__name__)

router = APIRouter()

@router.get('', response_model=AvailableModelsResponse)
async def ai_query(
    user_identity=Depends(get_active_user),
    ai_orm_context_client=Depends(get_ai_orm_context_client)
) -> AvailableModelsResponse:
    try:
        response = await ai_orm_context_client.get_models()
        return response
    except ModelResponseRemoteError as e:
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': e.message}
        )
    except Exception as e:
        logger.error(f'Unexpected available models response error: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )