from typing import Dict, Any

from connection_maker.driver_adapters.driver_adapter import DriverAdapter
from .auth_strategy import AuthStrategy, DBAPICreator


class SnowflakeJwtAuthStrategy(AuthStrategy):
    def make_creator(self, adapter: DriverAdapter, **kwargs) -> DBAPICreator:
        creds_provider = kwargs.get('creds_provider')
        if creds_provider is None:
            raise KeyError('Credentials provider not found')
        
        def _creator():
            credentials = creds_provider.creds()
            credentials_pwd = creds_provider.private_key_password()
            return adapter.connect(
                host=self.profile.host,
                port=self.profile.port,
                database=self.profile.database,
                username=self.profile.username,
                private_key_file=credentials,
                private_key_file_pwd=credentials_pwd,
                warehouse=self.profile.warehouse

            )
        return _creator
    
    def pool_settings(self) -> Dict[str, Any]:
        return {
            'pool_pre_ping': True, 
            'pool_recycle': 3000
        }
