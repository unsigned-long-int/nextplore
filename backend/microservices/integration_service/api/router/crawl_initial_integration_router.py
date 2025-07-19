from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from shared.contracts.integration_service import InitialCrawlRequest
from api.handlers import crawl_initial_integration_metadata


router = APIRouter(prefix='/v1/integration', tags=['Integration'])

@router.post('/crawl-initial')
def crawl_initial_integration(request: InitialCrawlRequest) -> JSONResponse:
    print(f'model posted: {request}')
    try:
        crawl_initial_integration_metadata(request)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={'success': True}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'success': False, 'message': str(e)}
        )
