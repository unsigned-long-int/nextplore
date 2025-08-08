import logging
from fastapi import APIRouter, Depends, status, HTTPException

from nextplore_shared.contracts.nextplore_orchestrator_service.ai_query_request import AIQueryRequest
from nextplore_shared.contracts.nextplore_orchestrator_service.ai_query_response import AIQueryResponse
from api.dependencies.authentication import get_active_user
from api.dependencies.microservices import (
    get_integration_client, 
    get_vector_client,
    get_embedding_client,
    get_ai_orm_context_client
)
from clients.ai_orm_context import ModelResponseRemoteError
from clients.embedding import EmbeddingResponseRemoteError
from internal_services.orm_factory.ai_query_processor import AIQueryProcessor

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post('', response_model=AIQueryResponse)
async def ai_query(
    request: AIQueryRequest, 
    user_identity=Depends(get_active_user),
    integration_client=Depends(get_integration_client),
    vector_client=Depends(get_vector_client),
    embedding_client=Depends(get_embedding_client),
    ai_orm_context_client=Depends(get_ai_orm_context_client)
) -> AIQueryResponse:
    try:
        processor = AIQueryProcessor(
            embedding_client=embedding_client,
            vector_client=vector_client,
            integration_client=integration_client,
            ai_orm_context_client=ai_orm_context_client,
            user_identity=user_identity
        )
        return await processor.run(request)
    except (ModelResponseRemoteError, EmbeddingResponseRemoteError) as e:
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': e.message}
        )
    except Exception as e:
        logger.error(f'ai query response error: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )