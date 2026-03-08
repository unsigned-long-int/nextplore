import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from nextplore_orchestrator.clients.llm_inference.models.model_info import ModelInfo
from nextplore_orchestrator.clients.llm_inference import ModelResponseRemoteError
from nextplore_orchestrator.api.dependencies.authentication import get_active_user
from nextplore_orchestrator.api.dependencies.microservices import get_llm_inference_client


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/nextplore-orchestrator', tags=['AiGenModels'])


@router.get('/llm-inference/models', response_model=List[ModelInfo])
async def get_gen_models(
    user_identity=Depends(get_active_user),
    llm_inference_client=Depends(get_llm_inference_client)
) -> ModelInfo:
    org_id = getattr(user_identity, 'organization_id', None)
    user_id = getattr(user_identity, 'user_id', None)
    try:
        response = await llm_inference_client.get_models(
            organization_id=org_id,
            user_id=user_id,
        )
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
