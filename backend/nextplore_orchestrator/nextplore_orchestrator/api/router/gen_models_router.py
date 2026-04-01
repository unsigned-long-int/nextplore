import logging
import asyncio
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from nextplore_orchestrator.clients.integration.exceptions import LlmGetProfilesRemoteError

from svc_nextplore_orchestrator_contracts.models import LlmProfile
from nextplore_orchestrator.clients.llm_inference import ModelResponseRemoteError
from nextplore_orchestrator.api.dependencies.authentication import get_active_user
from nextplore_orchestrator.api.dependencies.microservices import get_llm_inference_client, get_integration_client
from nextplore_orchestrator.domain.mappers import llm_profile_from_platform_model, llm_profile_from_user_model

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/nextplore-orchestrator', tags=['AiGenModels'])


@router.get('/llm-inference/models', response_model=List[LlmProfile])
async def get_gen_models(
    user_identity=Depends(get_active_user),
    llm_inference_client=Depends(get_llm_inference_client),
    integration_client=Depends(get_integration_client),
) -> List[LlmProfile]:
    org_id = getattr(user_identity, 'organization_id', None)
    user_id = getattr(user_identity, 'user_id', None)
    try:
        platform_models, user_models = await asyncio.gather(
            llm_inference_client.get_platform_models(organization_id=org_id, user_id=user_id),
            integration_client.get_user_llm_profiles(organization_id=org_id, user_id=user_id),
        )
        return [
            *map(llm_profile_from_platform_model, platform_models),
            *map(llm_profile_from_user_model, user_models),
        ]
    except (ModelResponseRemoteError, LlmGetProfilesRemoteError) as e:
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
            extra={'org_id': str(org_id), 'user_id': str(user_id)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
