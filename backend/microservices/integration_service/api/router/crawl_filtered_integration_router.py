from fastapi import APIRouter,  HTTPException, status

from nextplore_shared.cache.service_caches.integration_cache.cache import integration_service_cache
from nextplore_shared.contracts.integration_service.filtered_crawl_request import FilteredCrawlRequest
from nextplore_shared.contracts.integration_service.crawl_response import CrawlResponse
from services.integration_registry_crawl_service import CrawlIntegrationsFailed
from api.context import get_current_identity
from api.handlers import craw_filtered_integration_metadata


router = APIRouter(prefix='/v1/integration', tags=['Integration'])

@router.post('/crawl-filtered', response_model=CrawlResponse)
async def craw_filtered_integration(payload: FilteredCrawlRequest) -> CrawlResponse:
    user_identity = get_current_identity()
    cached = await integration_service_cache.get_filtered_integration(
        user_identity=user_identity,
        request=payload
    )
    if cached:
        return cached
    try:
        response = await craw_filtered_integration_metadata(payload)
        await integration_service_cache.set_filtered_integration(
            user_identity=user_identity,
            request=payload, 
            response=response
        )
        return response
    except CrawlIntegrationsFailed as e:
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={
                'message': e.message,
                'failed_integration_ids': [str(i) for i in e.failed_ids]
            }
        )
