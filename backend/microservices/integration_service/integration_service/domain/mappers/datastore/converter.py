from uuid import UUID

from svc_integration_contracts.models import (
    DataStoreCreateRequest,
    DataStoreUpdateRequest,
)

from integration_service.database.models import DataStoreORM
from integration_service.domain.models.datastore import (
    DataStore,
    DataStoreCreate,
    DataStoreProfile,
    DataStoreUpdate,
)


def datastore_update_from_dto(
    payload: DataStoreUpdateRequest,
) -> DataStoreUpdate:
    return DataStoreUpdate(
        connection_name=payload.connection_name,
        host=payload.host,
        port=payload.port,
        database_name=payload.database_name,
        autosync_on=payload.autosync_on,
    )


def datastore_create_from_dto(payload: DataStoreCreateRequest) -> DataStoreCreate:
    return DataStoreCreate(
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
        autosync_on=payload.autosync_on,
    )


def orm_from_datastore_create(
    organization_id: UUID, user_id: UUID, datastore_create: DataStoreCreate
) -> DataStoreORM:
    return DataStoreORM(
        organization_id=organization_id,
        user_id=user_id,
        auth=datastore_create.auth,
        cloud=datastore_create.cloud,
        db=datastore_create.db,
        connection_name=datastore_create.connection_name,
        descr=datastore_create.descr,
        host=datastore_create.host,
        port=datastore_create.port,
        database_name=datastore_create.database_name,
        warehouse=datastore_create.warehouse,
        tenant_id=datastore_create.tenant_id,
        client_id=datastore_create.client_id,
        region=datastore_create.region,
        azure_cert_kid=datastore_create.azure_cert_kid,
        azure_cert_name=datastore_create.azure_cert_name,
        azure_public_key_pem=datastore_create.azure_public_key_pem,
        snowflake_public_key_pem=datastore_create.snowflake_public_key_pem,
        kek_kid=datastore_create.kek_kid,
        autosync_on=datastore_create.autosync_on,
    )


def datastore_profile_from_orm(datastore_orm: DataStoreORM) -> DataStoreProfile:
    return DataStoreProfile(
        id=datastore_orm.id,
        auth=datastore_orm.auth,
        cloud=datastore_orm.cloud,
        db=datastore_orm.db,
        connection_name=datastore_orm.connection_name,
        database_name=datastore_orm.database_name,
        host=datastore_orm.host,
        port=datastore_orm.port,
        autosync_on=datastore_orm.autosync_on,
    )


def datastore_from_orm(datastore_orm: DataStoreORM) -> DataStore:
    return DataStore(
        id=datastore_orm.id,
        organization_id=datastore_orm.organization_id,
        user_id=datastore_orm.user_id,
        auth=datastore_orm.auth,
        cloud=datastore_orm.cloud,
        db=datastore_orm.db,
        connection_name=datastore_orm.connection_name,
        host=datastore_orm.host,
        database_name=datastore_orm.database_name,
        kek_kid=datastore_orm.kek_kid,
        port=datastore_orm.port,
        warehouse=datastore_orm.warehouse,
        tenant_id=datastore_orm.tenant_id,
        client_id=datastore_orm.client_id,
        region=datastore_orm.region,
        azure_cert_kid=datastore_orm.azure_cert_kid,
        azure_cert_name=datastore_orm.azure_cert_name,
        azure_public_key_pem=datastore_orm.azure_public_key_pem,
        snowflake_public_key_pem=datastore_orm.snowflake_public_key_pem,
        autosync_on=datastore_orm.autosync_on,
    )
