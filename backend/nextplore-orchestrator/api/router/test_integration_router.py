from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from internal_services.authentication import get_active_user
from shared.database.sql_connection_service import fetch_engine
from shared.database.connection_builder import build_connection_string, create_integration_metadata
from api.models import IntegrationCreateRequest


router = APIRouter()

@router.post('')
def test_integration(
    integration_create_request: IntegrationCreateRequest,
    user=Depends(get_active_user)
) -> JSONResponse:
    try:
        integration = create_integration_metadata(integration_create_request)
        connection_string = build_connection_string(integration)
        engine = fetch_engine(connection_string, connect_args={'connect_timeout': 5})

        with engine.connect() as connection:
            connection.execute(text('SELECT 1'))

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={'success': True}
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
        