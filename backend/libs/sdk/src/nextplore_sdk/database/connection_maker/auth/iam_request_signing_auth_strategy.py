from typing import Dict, Any

from nextplore_sdk.database.connection_maker.driver_adapters.driver_adapter import DriverAdapter
from .auth_strategy import AuthStrategy, DBAPICreator


class IamRequestSigningAuthStrategy(AuthStrategy):
    def make_creator(self, adapter: DriverAdapter, **kwargs: Any) -> DBAPICreator:
        def _creator():
            return adapter.connect(
                host=self.profile.host,
                port=self.profile.port,
                database=self.profile.database,
                username=self.profile.username,
            )
        return _creator
    
    def pool_settings(self) -> Dict[str, Any]:
        return {
            'pool_pre_ping': True, 
            'pool_recycle': 3000
        }
