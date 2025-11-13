import logging
from uuid import UUID
from fastapi import APIRouter,  HTTPException, status, Depends

from nextplore_sdk.database.connection_maker.engine.engine_manager import EngineManager
from nextplore_sdk.database.backend.database_backend_connector import DatabaseBackendConnector
from integration_service.api.models.filtered_crawl_request import FilteredCrawlRequest
from integration_service.api.models.crawl_response import CrawlResponse
from integration_service.services.crawl.exceptions import CrawlIntegrationsFailed
from integration_service.api.context import get_current_identity
from integration_service.api.handlers import craw_filtered_integration_metadata
from integration_service.cache import CacheService, get_cache_service
from integration_service.api.dependencies import get_backend_connector, get_engine_manager


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/integration', tags=['CrawlIntegration'])


@router.post('/organizations/{organization_id}/users/{user_id}/crawl', response_model=CrawlResponse)
async def craw_filtered_integration(
    organization_id: UUID,
    user_id: UUID,
    payload: FilteredCrawlRequest,
    cache_service: CacheService = Depends(get_cache_service),
    backend_connector: DatabaseBackendConnector = Depends(get_backend_connector),
    engine_manager: EngineManager = Depends(get_engine_manager)
) -> CrawlResponse:
    
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
        cached = await cache_service.get_filtered_integration(
            user_identity=user_identity,
            request=payload
        )
        if cached:
            return cached
        response = await craw_filtered_integration_metadata(
            user_id=user_identity.user_id,
            organization_id=user_identity.organization_id,
            inspection_request=payload,
            backend_connector=backend_connector,
            engine_manager=engine_manager
        )
        await cache_service.set_filtered_integration(
            user_identity=user_identity,
            request=payload, 
            response=response
        )
        return response
    except CrawlIntegrationsFailed as e:
        logger.error(
            f'Crawl integration failed for integrations: {e.failed_ids} with DB error: {e}', 
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': e.message}
        )
    except Exception as e:
        logger.error(f'Crawl integration unexpected error: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
    
