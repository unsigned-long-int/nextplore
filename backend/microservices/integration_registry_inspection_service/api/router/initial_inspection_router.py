from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from shared.contracts.integration_service import InitialInspectionRequest
from api.handlers import handle_initial_inspection


router = APIRouter(prefix='/v1/inspection', tags=['Inspection'])

@router.post('/inspect-initial')
def inspect_initial(request: InitialInspectionRequest) -> JSONResponse:
    print(f'model posted: {request}')
    try:
        handle_initial_inspection(request)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={'success': True}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'success': False, 'message': str(e)}
        )
