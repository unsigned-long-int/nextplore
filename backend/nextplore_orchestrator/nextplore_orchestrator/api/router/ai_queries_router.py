import logging
from fastapi import APIRouter, Depends, status, HTTPException

from nextplore_sdk.database.connection_maker.engine.engine_manager import EngineManager
from nextplore_orchestrator.api.models.ai_query_request import AIQueryRequest
from nextplore_orchestrator.api.models.ai_query_response import AIQueryResponse
from nextplore_orchestrator.api.dependencies.authentication import get_active_user
from nextplore_orchestrator.api.dependencies.microservices import (
    get_integration_client, 
    get_vector_client,
    get_embedding_client,
    get_llm_inference_client
)
from nextplore_orchestrator.api.dependencies.engine import get_engine_manager
from nextplore_orchestrator.clients.llm_inference import ModelResponseRemoteError
from nextplore_orchestrator.clients.embedding import EmbeddingResponseRemoteError
from nextplore_orchestrator.clients.integration import IntegrationGetRemoteError
from nextplore_orchestrator.clients.vector import VectorSearchDBRemoteError, VectorGetMetasRemoteError
from nextplore_orchestrator.services.orm_factory.exceptions import QueryRunError
from nextplore_orchestrator.services.orm_factory.ai_query_processor import AIQueryProcessor

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/nextplore-orchestrator', tags=['AiQuery'])


@router.post('/llm-inference/query', response_model=AIQueryResponse)
async def ai_query(
    request: AIQueryRequest, 
    user_identity=Depends(get_active_user),
    integration_client=Depends(get_integration_client),
    vector_client=Depends(get_vector_client),
    embedding_client=Depends(get_embedding_client),
    llm_inference_client=Depends(get_llm_inference_client),
    engine_manager: EngineManager = Depends(get_engine_manager)
) -> AIQueryResponse:
    org_id = getattr(user_identity, 'organization_id', None)
    user_id = getattr(user_identity, 'user_id', None)
    try:
        processor = AIQueryProcessor(
            embedding_client=embedding_client,
            vector_client=vector_client,
            integration_client=integration_client,
            llm_inference_client=llm_inference_client,
            user_identity=user_identity,
            engine_manager=engine_manager
        )
        return await processor.run(request)
    except (
        ModelResponseRemoteError, 
        EmbeddingResponseRemoteError, 
        IntegrationGetRemoteError, 
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
    except QueryRunError as e:
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
