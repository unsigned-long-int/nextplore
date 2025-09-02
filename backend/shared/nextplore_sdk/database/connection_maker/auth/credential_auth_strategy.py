from typing import Dict, Any

from connection_maker.driver_adapters.driver_adapter import DriverAdapter
from .auth_strategy import AuthStrategy, DBAPICreator


class CredentialAuthStrategy(AuthStrategy):
    def make_creator(self, adapter: DriverAdapter, **kwargs) -> DBAPICreator:
        creds_provider = kwargs.get('creds_provider')
        if creds_provider is None:
            raise KeyError('Credentials provider not found')
        
        def _creator():
            credentials = creds_provider.creds()
            return adapter.connect(
                host=self.profile.host,
                port=self.profile.port,
                database=self.profile.database,
                username=self.profile.username,
                password=credentials.secret,
                ca_path=self.profile.ca_path,
                timeout=10
            )
        return _creator
    
    def pool_settings(self) -> Dict[str, Any]:
        return {
            'pool_pre_ping': True, 
            'pool_recycle': 3000
        }