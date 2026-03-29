import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from integration_service.database.exceptions import UserLlmGetFailed
from integration_service.api.context import get_current_identity
from integration_service.services.llm import LlmService
from integration_service.api.dependencies import get_llm_service

from svc_integration_contracts.models import UserLlmProfile


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/integration', tags=['UserLlmProfiles'])


@router.get(
    '/organizations/{organization_id}/users/{user_id}/llm/profiles',
    response_model=List[UserLlmProfile]
)
async def get_user_llm_profiles(
        organization_id: UUID,
        user_id: UUID,
        llm_service: LlmService = Depends(get_llm_service),
) -> List[UserLlmProfile]:
    user_identity = get_current_identity()
    if user_identity.user_id != user_id or user_identity.organization_id != organization_id:
        logger.error(
            'Forbidden request',
            extra={'org_id': organization_id, 'user_id': user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={'message': 'Forbidden'}
        )
    try:

        user_llm_profiles = await llm_service.get_user_llm_profiles(user_identity)

        return [
            UserLlmProfile(
                api_base=user_llm.api_base,
                model_id=user_llm.model_id,
                label=user_llm.label,
                max_tokens=user_llm.max_tokens
            )
        for user_llm in user_llm_profiles]

    except UserLlmGetFailed as e:
        logger.error(
            f'Get user llm profiles request failed with DB error: {e}',
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': f'Database error: {str(e)}'}
        )
    except Exception as e:
        logger.error(
            f'Get user llm profiles failed with unexpected error: {str(e)}',
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
