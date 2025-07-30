from fastapi import APIRouter, status, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import JSONResponse

from shared.database.sql_connection_service import fetch_engine
from shared.database.connection_builder import build_connection_string, ConnectionMeta
from shared.contracts.integration_service import PreparedIntegrationTestRequest


router = APIRouter(prefix='/v1/integration', tags=['Integration'])

@router.post('/test-integration', status_code=status.HTTP_204_NO_CONTENT)
async def test_integration(payload: PreparedIntegrationTestRequest) -> None:
    try:
        connection_meta = ConnectionMeta(
            service_type=payload.service_type,
            auth_method=payload.auth_method,
            host=payload.host,
            port=payload.port,
            database_name=payload.database_name,
            username=payload.username,
            password=payload.password,
            kerberos_principal=payload.kerberos_principal,
            windows_domain=payload.windows_domain,
            extra_options=payload.extra_options
        )
        connection_string = build_connection_string(connection_meta)
        engine = fetch_engine(connection_string, connect_args={'connect_timeout': 5})

        with engine.connect() as connection:
            connection.execute(text('SELECT 1'))

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Database error: {str(e)}'
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Unhandled error: {str(e)}'
        )

        