from uuid import UUID
from typing import List

from domain_models import Integration
from database.models import IntegrationSecretMvORM
from nextplore_sdk.contracts.integration_service.integration_connection_profile import IntegrationConnectionProfile
from nextplore_sdk.contracts.integration_service.prepared_integration_create_request import PreparedIntegrationCreateRequest


def to_domain_integration(
    organization_id: UUID,
    user_id: UUID,
    integration_create_request: PreparedIntegrationCreateRequest
) -> Integration:
    return Integration(
        organization_id=organization_id,
        user_id=user_id,
        auth=integration_create_request.auth,
        cloud=integration_create_request.cloud,
        db=integration_create_request.db,
        connection_name=integration_create_request.connection_name,
        host=integration_create_request.host,
        database_name=integration_create_request.database_name,
        port=integration_create_request.port,
        warehouse=integration_create_request.warehouse,
        tenant_id=integration_create_request.tenant_id,
        client_id=integration_create_request.client_id,
        region=integration_create_request.region,
        azure_cert_kid=integration_create_request.azure_cert_kid,
        azure_public_key_pem=integration_create_request.azure_public_key_pem,
        snowflake_public_key_pem=integration_create_request.snowflake_public_key_pem,
        autosync_on=integration_create_request.autosync_on
    )


def to_integration_connection_profile(integration_mv_orm: List[IntegrationSecretMvORM]) -> IntegrationConnectionProfile:
    return IntegrationConnectionProfile(
        auth=integration_mv_orm.auth,
        cloud=integration_mv_orm.cloud,
        db=integration_mv_orm.db,
        host=integration_mv_orm.host,
        database_name=integration_mv_orm.database_name,
        port=integration_mv_orm.port,
        warehouse=integration_mv_orm.warehouse,


    )
