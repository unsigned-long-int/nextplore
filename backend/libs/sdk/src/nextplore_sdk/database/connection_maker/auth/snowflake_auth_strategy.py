from typing import Dict, Any

from nextplore_sdk.database.connection_maker.driver_adapters.driver_adapter import DriverAdapter
from .auth_strategy import AuthStrategy, DBAPICreator


class SnowflakeAuthStrategy(AuthStrategy):
    def make_creator(self, adapter: DriverAdapter, **kwargs: Any) -> DBAPICreator:
        creds_provider = kwargs.get('creds_provider')
        if creds_provider is None:
            raise KeyError('Credentials provider not found')
        
        def _creator():
            credentials = creds_provider.creds()
            return adapter.connect(
                host=self.profile.host,
                database=self.profile.database,
                username=self.profile.username,
                password=credentials,
                warehouse=self.profile.warehouse

            )
        return _creator
    
    def pool_settings(self) -> Dict[str, Any]:
        return {
            'pool_pre_ping': True, 
            'pool_recycle': 3000
        }
