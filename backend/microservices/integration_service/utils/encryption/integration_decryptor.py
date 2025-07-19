from shared.encryptor import decrypt_secret
from .encrypted_integration import EncryptedIntegration
from .decrypted_integration import DecryptedIntegration


def decrypt_integration(integration: EncryptedIntegration) -> DecryptedIntegration:
    return DecryptedIntegration(
        integration_id=integration.integration_id,
        organization_id = integration.organization_id,
        user_id = integration.user_id,
        service_type = integration.service_type,
        auth_method = integration.auth_method,
        connection_name = integration.connection_name,
        host = integration.host,
        port = integration.port,
        database_name = integration.database_name,
        username=decrypt_secret(integration.encrypted_username) if integration.encrypted_username else '',
        password=decrypt_secret(integration.encrypted_password) if integration.encrypted_password else '',
        kerberos_principal=decrypt_secret(integration.encrypted_kerberos_principal) if integration.encrypted_kerberos_principal else '',
        windows_domain=decrypt_secret(integration.encrypted_windows_domain) if integration.encrypted_windows_domain else '',
        extra_options=decrypt_secret(integration.encrypted_extra_options) if integration.encrypted_extra_options else '',
        autosync_on=integration.autosync_on
    )
