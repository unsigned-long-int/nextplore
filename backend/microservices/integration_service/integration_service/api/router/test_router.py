import logging
from fastapi import APIRouter, status, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from svc_integration_contracts.models import IntegrationCreateRequest
from nextplore_sdk.database.connection_maker.engine.engine_manager import EngineManager
from nextplore_sdk.database.connection_maker.models.connection_profile import ConnectionProfile
from nextplore_sdk.database.connection_maker.mappers.to_domain_cloud import to_domain_cloud
from nextplore_sdk.database.connection_maker.mappers.to_domain_auth import to_domain_auth
from nextplore_sdk.database.connection_maker.mappers.to_domain_db import to_domain_db


from integration_service.api.dependencies import get_engine_manager



logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/integration', tags=['TestIntegration'])


@router.post('/test', status_code=status.HTTP_204_NO_CONTENT)
async def test_integration(
    payload: IntegrationCreateRequest,
    engine_manager: EngineManager = Depends(get_engine_manager)
) -> None:
    try:
        connection_profile = ConnectionProfile(
            cloud=to_domain_cloud(payload.cloud.value),
            auth=to_domain_auth(payload.auth.value),
            db=to_domain_db(payload.db.value),
            host=payload.host,
            database=payload.database_name,
            port=payload.port,
            warehouse=payload.warehouse,
            username=payload.username.get_secret_value() if payload.username else None,
            password=payload.password.get_secret_value() if payload.password else None,
            client_secret=payload.client_secret.get_secret_value() if payload.client_secret else None,
            aws_external_id=payload.aws_external_id.get_secret_value() if payload.aws_external_id else None,
            aws_role_arn=payload.aws_role_arn.get_secret_value() if payload.aws_role_arn else None,
            snowflake_private_key=payload.snowflake_private_key.get_secret_value() if payload.snowflake_private_key else None,
            azure_cert_kid=payload.azure_cert_kid,
            azure_cert_name=payload.azure_cert_name,
            tenant_id=payload.tenant_id,
            client_id=payload.client_id,
            region=payload.region
        )
        engine = await engine_manager.acquire_engine(connection_profile)

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
