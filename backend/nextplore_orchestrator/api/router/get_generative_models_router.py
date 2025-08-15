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
    org_id = getattr(user_identity, 'organization_id', None)
    user_id = getattr(user_identity, 'user_id', None)
    try:
        response = await ai_orm_context_client.get_models()
        return response
    except ModelResponseRemoteError as e:
        logger.error(
            'AI models retrieval failed (remote)',
            extra={'org_id': str(org_id), 'user_id': str(user_id)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )
    except Exception as e:
        logger.error(
            'AI models retrieval failed (unexpected)',
            extra={'org_id': str(org_id), 'user_id': str(user_id)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )