import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from integration_service.database.exceptions import UserLlmGetFailed
from integration_service.api.context import get_current_identity
from integration_service.services.llm import LlmService
from integration_service.api.dependencies import get_llm_service

from svc_integration_contracts.models import UserLlmConfig


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/integration', tags=['UserLlmConfig'])


@router.get(
    '/organizations/{organization_id}/users/{user_id}/llm/{model_id}/config',
    response_model=UserLlmConfig
)
async def get_user_llm_configs(
        organization_id: UUID,
        user_id: UUID,
        model_id: UUID,
        llm_service: LlmService = Depends(get_llm_service),
) -> UserLlmConfig:
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
        user_llm_config = await llm_service.get_user_llm_config(
            user_identity=user_identity,
            model_id=model_id
        )
        return user_llm_config
    except UserLlmGetFailed as e:
        logger.error(
            f'Get user llm config request failed with DB error: {e}',
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': f'Database error: {str(e)}'}
        )
    except Exception as e:
        logger.error(
            f'Get user llm config failed with unexpected error: {str(e)}',
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
