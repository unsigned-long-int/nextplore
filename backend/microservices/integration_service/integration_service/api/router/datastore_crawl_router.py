import logging
from uuid import UUID
from fastapi import APIRouter,  HTTPException, status, Depends
from svc_integration_contracts.models import FilteredCrawlRequest, CrawlResponse
from nextplore_sdk.database.connection_maker.engine.engine_manager import EngineManager

from integration_service.database.repositories import DataStoreRepository
from integration_service.services.crawl.exceptions import CrawlDataStoresFailed
from integration_service.api.context import get_current_identity
from integration_service.api.handlers import crawl_filtered_datastore_metadata
from integration_service.cache import CacheService, get_cache_service
from integration_service.api.dependencies import get_engine_manager, get_data_stores_integration_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/integration', tags=['CrawlDataStore'])


@router.post('/organizations/{organization_id}/users/{user_id}/datastores/crawl', response_model=CrawlResponse)
async def craw_filtered_datastore(
    organization_id: UUID,
    user_id: UUID,
    payload: FilteredCrawlRequest,
    cache_service: CacheService = Depends(get_cache_service),
    repo: DataStoreRepository = Depends(get_data_stores_integration_repo),
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
        cached = await cache_service.get_filtered_datastore(
            user_identity=user_identity,
            request=payload
        )
        if cached:
            return cached
        response = await crawl_filtered_datastore_metadata(
            user_id=user_identity.user_id,
            organization_id=user_identity.organization_id,
            inspection_request=payload,
            repo=repo,
            engine_manager=engine_manager
        )
        await cache_service.set_filtered_datastore(
            user_identity=user_identity,
            request=payload, 
            response=response
        )
        return response
    except CrawlDataStoresFailed as e:
        logger.error(
            f'Crawl data store failed for integrations: {e.failed_ids} with DB error: {e}',
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': e.message}
        )
    except Exception as e:
        logger.error(f'Crawl data store unexpected error: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
    
