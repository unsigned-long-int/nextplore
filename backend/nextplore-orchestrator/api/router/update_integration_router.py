from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from shared.database.repositories import IntegrationRepository, IntegrationUpdateFailed
from internal_services.authentication import get_active_user
from internal_services.identity_service import resolve_user_identity
from api.models import IntegrationUpdateRequest


router = APIRouter()

@router.post('')
def update_integration(
    integration_update_request: IntegrationUpdateRequest,
    user=Depends(get_active_user)
) -> JSONResponse:
    azure_tenant_id = user.get('tid')
    azure_user_id = user.get('oid')

    user_identity = resolve_user_identity(azure_tenant_id, azure_user_id)

    integration_repo = IntegrationRepository()
    try:
        integration_repo.update_integration(user_identity, integration_update_request)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={'success': True}
        )
    
    except IntegrationUpdateFailed as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'success': False, 'message': str(e)}
        )
    except SQLAlchemyError as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'success': False, 'message': str(e)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'success': False, 'message': str(e)}
        )
