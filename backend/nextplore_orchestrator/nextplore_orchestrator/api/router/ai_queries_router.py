import logging
import asyncio
from fastapi import APIRouter, Depends, status, HTTPException

from nextplore_orchestrator.api.context import UserIdentity
from nextplore_orchestrator.api.dependencies.cache import get_orchestrator_cache_service
from nextplore_orchestrator.api.dependencies.llm_orchestrator import get_llm_orchestrator_factory
from nextplore_orchestrator.api.dependencies.cache import get_semantic_cache_service
from nextplore_orchestrator.api.dependencies.microservices import get_integration_client, get_embedding_client
from nextplore_orchestrator.api.models.ai_query_request import AIQueryRequest
from nextplore_orchestrator.api.models.ai_query_response import AIQueryResponse
from nextplore_orchestrator.api.dependencies.authentication import get_active_user
from nextplore_orchestrator.cache.orchestrator_cache import OrchestratorCacheService
from nextplore_orchestrator.cache.semantic_cache_service import SemanticCacheService
from nextplore_orchestrator.clients.llm_inference import ModelResponseRemoteError
from nextplore_orchestrator.clients.embedding import EmbeddingResponseRemoteError, EmbeddingClient
from nextplore_orchestrator.clients.integration import DataStoreGetRemoteError, IntegrationClient
from nextplore_orchestrator.clients.vector import VectorSearchDBRemoteError, VectorGetMetasRemoteError
from nextplore_orchestrator.domain.mappers import base_llm_spec_from_query_request, user_llm_spec_from_llm_config
from nextplore_orchestrator.services.query_orchestrator.exceptions import QueryRunError, LlmOrchestratorBootstrapError
from nextplore_orchestrator.services.query_orchestrator.llm_orchestrator import LlmOrchestratorFactory

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/nextplore-orchestrator', tags=['AiQuery'])


@router.post('/llm-inference/query', response_model=AIQueryResponse)
async def ai_query(
    request: AIQueryRequest, 
    user_identity: UserIdentity = Depends(get_active_user),
    llm_orchestrator_factory: LlmOrchestratorFactory = Depends(get_llm_orchestrator_factory),
    embedding_client: EmbeddingClient = Depends(get_embedding_client),
    integration_client: IntegrationClient = Depends(get_integration_client),
    cache_service: OrchestratorCacheService = Depends(get_orchestrator_cache_service),
    semantic_cache_service: SemanticCacheService = Depends(get_semantic_cache_service),
) -> AIQueryResponse:
    org_id = getattr(user_identity, 'organization_id', None)
    user_id = getattr(user_identity, 'user_id', None)
    try:
        embedding_response = await embedding_client.embed(request.prompt)

        if not request.bypass_cache:
            cached = await cache_service.get_ai_query_response(
                user_identity=user_identity,
                request=request
            )
            if cached:
                cached.cache_hit = True
                return cached

            sem_cache_lookup_result = await semantic_cache_service.lookup_semantic_cache(
                ai_query=request,
                embedding=embedding_response.embedding,
                user_identity=user_identity,
            )
            if sem_cache_lookup_result:
                response = AIQueryResponse.model_validate(sem_cache_lookup_result.json_payload)
                response.cache_hit = True
                return response

        llm_spec = base_llm_spec_from_query_request(
            query_request=request,
            base_prompt_embedding=embedding_response.embedding
        )

        if request.is_user_model:
            user_llm_config = await integration_client.get_user_llm_config(
                organization_id=org_id,
                user_id=user_id,
                model_id=request.model_ref_id
            )
            llm_spec.user_llm_config = user_llm_spec_from_llm_config(user_llm_config)
        llm_orchestrator = llm_orchestrator_factory.get_llm_orchestrator(request.mode)

        response = await llm_orchestrator.run(
            llm_spec=llm_spec,
            user_identity=user_identity
        )


        if not request.bypass_cache:
            coros = [
                cache_service.set_ai_query_response(
                    user_identity=user_identity,
                    request=request,
                    response=response
                ),
                semantic_cache_service.store_semantic_cache_entry(
                    embedding=embedding_response.embedding,
                    request=request,
                    response=response,
                    user_identity=user_identity,
                )
            ]
            await asyncio.gather(*coros)


        return response
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
