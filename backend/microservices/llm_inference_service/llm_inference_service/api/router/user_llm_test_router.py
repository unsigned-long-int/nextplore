import logging
from uuid import UUID
from fastapi import APIRouter, status, HTTPException

from llm_inference_service.services.models_gateway.provider_factory import dispatch_provider_factory
from llm_inference_service.api.context import get_current_identity
from llm_inference_service.domain.mappers.model_gateway_params import user_llm_params_from_dto
from llm_inference_service.services.models_gateway.exceptions import InvalidModelResponse
from svc_llm_inference_contracts.models import UserLlmTestRequest


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/llm-inference', tags=['LlmTest'])


@router.post('/organizations/{organization_id}/users/{user_id}/llm/test', status_code=status.HTTP_204_NO_CONTENT)
async def test_user_llm(
    organization_id: UUID,
    user_id: UUID,
    payload: UserLlmTestRequest
) -> None:
    user_identity = get_current_identity()

    if organization_id != user_identity.organization_id or user_id != user_identity.user_id:
        logger.error(
            'Forbidden request',
            extra={'ord_id': organization_id, 'user_id': user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={'message': 'Forbidden'}
        )
    try:

        params = user_llm_params_from_dto(payload)
        provider_factory = dispatch_provider_factory(params)
        provider = provider_factory.create()
        response = await provider.prompt_model('Hi!', max_tokens=1)
        if not response:
            msg = f'Test custom llm failed for model: {params.model_id}'
            logger.error(
                msg,
                extra={
                    'organization_id': user_identity.organization_id,
                    'user_id': user_identity.user_id,
                    'model_id': payload.model_id
                }
            )
            raise InvalidModelResponse(msg)
    except InvalidModelResponse as e:
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': f'Llm response error: {str(e)}'}
        )
    except Exception as e:
        logger.error(
            f'Unexpected llm test error: {str(e)}.',
            extra={
                'organization_id': user_identity.organization_id,
                'user_id': user_identity.user_id,
                'model_id': payload.model_id,
                'error_type': type(e).__name__,
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )