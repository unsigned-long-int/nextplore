#from api.models import IntegrationCreateRequest
from shared.database.models import IntegrationORM
from shared.encryption import decrypt_secret
from .integration_metadata import IntegrationMetadata

def _(integration) -> IntegrationMetadata:
    return IntegrationMetadata(**integration.model_dump())

def create_integration_metadata(integration: IntegrationORM) -> IntegrationMetadata:
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
