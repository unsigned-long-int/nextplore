import logging
from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException

from integration_service.api.context import get_current_identity
from integration_service.api.dependencies import get_llm_service
from integration_service.database.exceptions import UserLlmCreateFailed
from integration_service.services.llm import LlmService

from svc_integration_contracts.models import UserLlmCreateRequest


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/integration', tags=['Llm'])


@router.post(
    '/organizations/{organization_id}/users/{user_id}/llm',
    status_code=status.HTTP_201_CREATED,
)
async def create_user_llm(
    organization_id: UUID,
    user_id: UUID,
    payload: UserLlmCreateRequest,
    llm_service: LlmService = Depends(get_llm_service)
) -> None:
    user_identity = get_current_identity()

    if organization_id != user_identity.organization_id or user_id != user_identity.user_id:
        logger.error(
            'Forbidden request',
            extra={'org_id': organization_id, 'user_id': user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={'message': 'Forbidden'}
        )
    try:
        await llm_service.create_user_llm(
            user_identity=user_identity,
            payload=payload,
        )
    except UserLlmCreateFailed as e:
        logger.error(
            f'Create LLM model failed with DB error: {str(e)}',
            exc_info=True
        )

        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': f'Database error: {str(e)}'}
        )
    except Exception as e:
        logger.error(
            f'Unexpected create LLM model error: {str(e)}',
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error while creating integration: {str(e)}'}
        )
