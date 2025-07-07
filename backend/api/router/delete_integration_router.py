from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from services.database.repositories import IntegrationRepository, IntegrationDeleteFailed
from services.authentication import get_active_user
from services.identity_service import resolve_user_identity
from api.models import IntegrationDeleteRequest


router = APIRouter()

@router.post('')
def delete_integration(
    integration_delete_request: IntegrationDeleteRequest,
    user=Depends(get_active_user)
) -> JSONResponse:
    azure_tenant_id = user.get('tid')
    azure_user_id = user.get('oid')

    user_identity = resolve_user_identity(azure_tenant_id, azure_user_id)

    integration_repo = IntegrationRepository()
    try:
        integration_repo.delete_integration(user_identity, integration_delete_request)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={'success': True}
        )
    
    except IntegrationDeleteFailed as e:
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
