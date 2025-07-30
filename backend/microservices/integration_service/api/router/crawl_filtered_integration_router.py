from fastapi import APIRouter

from shared.cache.service_caches.integration_cache import integration_service_cache
from shared.contracts.integration_service import FilteredCrawlRequest, CrawlResponse
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

    response = await craw_filtered_integration_metadata(payload)
    await integration_service_cache.set_filtered_integration(
        user_identity=user_identity,
        request=payload, 
        response=response
    )
    return response
