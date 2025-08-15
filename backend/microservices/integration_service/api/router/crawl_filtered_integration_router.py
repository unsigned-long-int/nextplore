import logging
from fastapi import APIRouter,  HTTPException, status, Depends

from nextplore_sdk.contracts.integration_service.filtered_crawl_request import FilteredCrawlRequest
from nextplore_sdk.contracts.integration_service.crawl_response import CrawlResponse
from services.integration_registry_crawl_service import CrawlIntegrationsFailed
from api.context import get_current_identity
from api.handlers import craw_filtered_integration_metadata
from cache import CacheService, get_cache_service


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/integration', tags=['Integration'])

@router.post('/crawl-filtered', response_model=CrawlResponse)
async def craw_filtered_integration(
    payload: FilteredCrawlRequest,
    cache_service: CacheService = Depends(get_cache_service)
) -> CrawlResponse:
    try:
        user_identity = get_current_identity()
        cached = await cache_service.get_filtered_integration(
            user_identity=user_identity,
            request=payload
        )
        if cached:
            return cached
        response = await craw_filtered_integration_metadata(
            user_id=user_identity.user_id,
            organization_id=user_identity.organization_id,
            inspection_request=payload
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
    
