import json 

from nextplore_sdk.encryptor.encryption import encrypt_secret
from .encrypted_integration import EncryptedIntegration
from .decrypted_integration import DecryptedIntegration


def encrypt_integration(integration: DecryptedIntegration) -> EncryptedIntegration:
    return EncryptedIntegration(
        organization_id = integration.organization_id,
        user_id = integration.user_id,
        service_type = integration.service_type,
        auth_method = integration.auth_method,
        connection_name = integration.connection_name,
        host = integration.host,
        port = integration.port,
        database_name = integration.database_name,
        encrypted_username = encrypt_secret(integration.username) if integration.username else None,
        encrypted_password = encrypt_secret(integration.password) if integration.password else None,
        encrypted_kerberos_principal = encrypt_secret(integration.kerberos_principal) if integration.kerberos_principal else None,
        encrypted_windows_domain = encrypt_secret(integration.windows_domain) if integration.windows_domain else None,
        encrypted_extra_options = encrypt_secret(json.dumps(integration.extra_options)) if integration.extra_options else None,
        autosync_on=integration.autosync_on
    )
