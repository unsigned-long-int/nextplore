from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from shared.database.repositories import IntegrationRepository, IntegrationUpdateFailed
from internal_services.authentication import get_active_user
from shared.encryption import ENCRYPTED_FIELDS, encrypt_secret
from shared.identity_service import resolve_user_identity
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
        update_args = {
            field: encrypt_secret(value) if field in ENCRYPTED_FIELDS else value for field, value in integration_update_request.model_dump().items()
            if value is not None and field != 'id'
        }
        integration_repo.update_integration(
            user_identity=user_identity, 
            integration_id=integration_update_request.id, 
            update_args=update_args
        )

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
