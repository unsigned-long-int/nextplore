import logging
from fastapi import APIRouter, Depends, status, HTTPException


from nextplore_orchestrator.api.dependencies.llm_orchestrator.get_llm_orchestrator_factory import \
    get_llm_orchestrator_factory
from nextplore_orchestrator.api.dependencies.microservices import get_integration_client
from nextplore_orchestrator.api.models.ai_query_request import AIQueryRequest
from nextplore_orchestrator.api.models.ai_query_response import AIQueryResponse
from nextplore_orchestrator.api.dependencies.authentication import get_active_user
from nextplore_orchestrator.clients.llm_inference import ModelResponseRemoteError
from nextplore_orchestrator.clients.embedding import EmbeddingResponseRemoteError
from nextplore_orchestrator.clients.integration import DataStoreGetRemoteError
from nextplore_orchestrator.clients.vector import VectorSearchDBRemoteError, VectorGetMetasRemoteError
from nextplore_orchestrator.domain.mappers import base_llm_spec_from_query_request
from nextplore_orchestrator.services.query_orchestrator.exceptions import QueryRunError, LlmOrchestratorBootstrapError


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/nextplore-orchestrator', tags=['AiQuery'])


@router.post('/llm-inference/query', response_model=AIQueryResponse)
async def ai_query(
    request: AIQueryRequest, 
    user_identity=Depends(get_active_user),
    llm_orchestrator_factory=Depends(get_llm_orchestrator_factory),
    integration_client=Depends(get_integration_client),
) -> AIQueryResponse:
    org_id = getattr(user_identity, 'organization_id', None)
    user_id = getattr(user_identity, 'user_id', None)
    try:
        llm_spec = base_llm_spec_from_query_request(request)
        if request.is_user_model:
            user_llm_config = await integration_client.get_user_llm_config(
                organization_id=org_id,
                user_id=user_id,
                model_id=request.model_ref_id
            )
            llm_spec.user_llm_config = user_llm_config
        llm_orchestrator = llm_orchestrator_factory.get_llm_orchestrator(request.mode)
        return await llm_orchestrator.run(
            llm_spec=llm_spec,
            user_identity=user_identity
        )
    except (
        ModelResponseRemoteError, 
        EmbeddingResponseRemoteError, 
        DataStoreGetRemoteError,
        VectorSearchDBRemoteError,
        VectorGetMetasRemoteError
    ) as e:
        logger.error(
            'AI query failed (remote)',
            extra={'org_id': org_id, 'user_id': user_id},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )
    except (QueryRunError, LlmOrchestratorBootstrapError) as e:
        logger.error(
            'AI query failed (local)',
            extra={'org_id': org_id, 'user_id': user_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )
    except Exception as e:
        logger.error(
            'AI Query failed (unexpected)',
            extra={'org_id': str(org_id), 'user_id': str(user_id)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
