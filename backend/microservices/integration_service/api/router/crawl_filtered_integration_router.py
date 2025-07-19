from fastapi import APIRouter

from shared.contracts.integration_service import FilteredCrawlRequest, CrawlResponse
from api.handlers import craw_filtered_integration_metadata


router = APIRouter(prefix='/v1/integration', tags=['Integration'])

@router.post('/crawl-filtered', response_model=CrawlResponse)
def craw_filtered_integration(request: FilteredCrawlRequest) -> CrawlResponse:
    return craw_filtered_integration_metadata(request)
