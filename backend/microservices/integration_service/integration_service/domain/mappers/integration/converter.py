from uuid import UUID
from svc_integration_contracts.models import (
    IntegrationUpdateRequest,
    IntegrationCreateRequest
)

from integration_service.domain.models.integration import (
    IntegrationUpdate,
    IntegrationCreate,
    IntegrationProfile,
    Integration
)
from integration_service.database.models import IntegrationORM


def integration_update_from_dto(
    payload: IntegrationUpdateRequest
) -> IntegrationUpdate:
    return IntegrationUpdate(
        connection_name=payload.connection_name,
        host=payload.host,
        port=payload.port,
        database_name=payload.database_name,
        autosync_on=payload.autosync_on
    )


def integration_create_from_dto(payload: IntegrationCreateRequest) -> IntegrationCreate:
    return IntegrationCreate(
        auth=payload.auth,
        cloud=payload.cloud,
        db=payload.db,
        connection_name=payload.connection_name,
        descr=payload.descr,
        host=payload.host,
        database_name=payload.database_name,
        kek_kid=payload.kek_kid,
        port=payload.port,
        warehouse=payload.warehouse,
        tenant_id=payload.tenant_id,
        client_id=payload.client_id,
        region=payload.region,
        azure_cert_kid=payload.azure_cert_kid,
        azure_cert_name=payload.azure_cert_name,
        azure_public_key_pem=payload.azure_public_key_pem,
        snowflake_public_key_pem=payload.snowflake_public_key_pem,
        autosync_on=payload.autosync_on
    )


def orm_from_integration_create(
    organization_id: UUID,
    user_id: UUID,
    integration_create: IntegrationCreate
) -> IntegrationORM:
    return IntegrationORM(
        organization_id=organization_id,
        user_id=user_id,
        auth=integration_create.auth,
        cloud=integration_create.cloud,
        db=integration_create.db,
        connection_name=integration_create.connection_name,
        descr=integration_create.descr,
        host=integration_create.host,
        port=integration_create.port,
        database_name=integration_create.database_name,
        warehouse=integration_create.warehouse,
        tenant_id=integration_create.tenant_id,
        client_id=integration_create.client_id,
        region=integration_create.region,
        azure_cert_kid=integration_create.azure_cert_kid,
        azure_cert_name=integration_create.azure_cert_name,
        azure_public_key_pem=integration_create.azure_public_key_pem,
        snowflake_public_key_pem=integration_create.snowflake_public_key_pem,
        kek_kid=integration_create.kek_kid,
        autosync_on=integration_create.autosync_on
    )


def integration_profile_from_orm(integration_orm: IntegrationORM) -> IntegrationProfile:
    return IntegrationProfile(
        id=integration_orm.id,
        auth=integration_orm.auth,
        cloud=integration_orm.cloud,
        db=integration_orm.db,
        connection_name=integration_orm.connection_name,
        database_name=integration_orm.database_name,
        host=integration_orm.host,
        port=integration_orm.port,
        autosync_on=integration_orm.autosync_on
    )


def integration_from_orm(integration_orm: IntegrationORM) -> Integration:
    return Integration(
        id=integration_orm.id,
        organization_id=integration_orm.organization_id,
        user_id=integration_orm.user_id,
        auth=integration_orm.auth,
        cloud=integration_orm.cloud,
        db=integration_orm.db,
        connection_name=integration_orm.connection_name,
        host=integration_orm.host,
        database_name=integration_orm.database_name,
        kek_kid=integration_orm.kek_kid,
        port=integration_orm.port,
        warehouse=integration_orm.warehouse,
        tenant_id=integration_orm.tenant_id,
        client_id=integration_orm.client_id,
        region=integration_orm.region,
        azure_cert_kid=integration_orm.azure_cert_kid,
        azure_cert_name=integration_orm.azure_cert_name,
        azure_public_key_pem=integration_orm.azure_public_key_pem,
        snowflake_public_key_pem=integration_orm.snowflake_public_key_pem,
        autosync_on=integration_orm.autosync_on
    )
