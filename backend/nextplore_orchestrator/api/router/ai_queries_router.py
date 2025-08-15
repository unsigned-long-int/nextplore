import logging
from fastapi import APIRouter, Depends, status, HTTPException

from nextplore_sdk.contracts.nextplore_orchestrator_service.ai_query_request import AIQueryRequest
from nextplore_sdk.contracts.nextplore_orchestrator_service.ai_query_response import AIQueryResponse
from api.dependencies.authentication import get_active_user
from api.dependencies.microservices import (
    get_integration_client, 
    get_vector_client,
    get_embedding_client,
    get_ai_orm_context_client
)
from clients.ai_orm_context import ModelResponseRemoteError
from clients.embedding import EmbeddingResponseRemoteError
from clients.integration import IntegrationGetRemoteError
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
    org_id = getattr(user_identity, 'organization_id', None)
    user_id = getattr(user_identity, 'user_id', None)
    try:
        processor = AIQueryProcessor(
            embedding_client=embedding_client,
            vector_client=vector_client,
            integration_client=integration_client,
            ai_orm_context_client=ai_orm_context_client,
            user_identity=user_identity
        )
        return await processor.run(request)
    except (ModelResponseRemoteError, EmbeddingResponseRemoteError, IntegrationGetRemoteError) as e:
        logger.error(
            'AI query failed (remote)',
            extra={'org_id': str(org_id), 'user_id': str(user_id)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )
    except Exception as e:
        logger.error(
            'AI Query failed (unexpected)',
            extra={'org_id': str(org_id), 'user_id': str(user_id)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )