from typing import Any

from .credentials_provider import CredentialsProvider


class SnowflakePrivateKeyCredentialsProvider(CredentialsProvider):

    def creds(self, **_: Any) -> str:
        return self._private_key()

    def private_key_password(self) -> str:
        return 'MigrateMe2024!'
    
    def _private_key(self) -> str:
        return self.profile.snowflake_private_key

    #def _private_key_file(self) -> str:
    #    return '/Users/nik/Downloads/rsa_key.p8'