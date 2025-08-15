import logging
from fastapi import APIRouter, status, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from nextplore_sdk.database.sql_connection_service.session_starter import fetch_engine
from nextplore_sdk.database.connection_builder.database_connection_builder import build_connection_string, ConnectionMeta
from nextplore_sdk.contracts.integration_service.prepared_integration_test_request import PreparedIntegrationTestRequest


logger = logging.getLogger(__name__)

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
        logger.error(
            f'Test integration failed with DB error: {e}', 
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': f'Database error: {str(e)}'}
        )
    except Exception as e:
        logger.error(
            f'Unexpected test integration error: {e}', 
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
