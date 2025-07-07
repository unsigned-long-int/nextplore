from functools import singledispatch
from typing import Set

from api.models import IntegrationCreateRequest, IntegrationUpdateRequest
from services.database.models import IntegrationORM
from services.encryption import decrypt_secret
from .integration_metadata import IntegrationMetadata


@singledispatch
def create_integration_metadata(integration) -> IntegrationMetadata:
    raise NotImplementedError

@create_integration_metadata.register
def _(integration: IntegrationCreateRequest) -> IntegrationMetadata:
    return IntegrationMetadata(**integration.model_dump())

@create_integration_metadata.register
def _(integration: IntegrationORM) -> IntegrationMetadata:
    return IntegrationMetadata(
        service_type=integration.service_type,
        auth_method=integration.auth_method,
        connection_name=integration.connection_name,
        host=integration.host,
        port=integration.port,
        database_name=integration.database_name,
        username=decrypt_secret(integration.encrypted_username) if integration.encrypted_username else '',
        password=decrypt_secret(integration.encrypted_password) if integration.encrypted_password else '',
        kerberos_principal=decrypt_secret(integration.encrypted_kerberos_principal) if integration.encrypted_kerberos_principal else '',
        windows_domain=decrypt_secret(integration.encrypted_windows_domain) if integration.encrypted_windows_domain else '',
        extra_options=decrypt_secret(integration.encrypted_extra_options) if integration.encrypted_extra_options else '',
        autosync_on=integration.autosync_on
    )

@create_integration_metadata.register
def _(integration: IntegrationUpdateRequest) -> IntegrationMetadata:
    update_fields = {
        field: value
        for field, value in integration.dump_model().items()
        if field != 'id'
    }
    return IntegrationMetadata(
        **update_fields
    )
