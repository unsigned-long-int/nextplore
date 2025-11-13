from typing import Dict, Any, ClassVar

from nextplore_sdk.database.connection_maker.ca_bundle_resolver.resolver import resolve_ca_bundle
from nextplore_sdk.database.connection_maker.utils.token_bytes_maker import make_token_bytes
from nextplore_sdk.database.connection_maker.driver_adapters.driver_adapter import DriverAdapter
from .auth_strategy import AuthStrategy, DBAPICreator


class AzureIamAsqlStrategy(AuthStrategy):
    ACCESS_TOKEN_ATTR: ClassVar[int] = 1256
    SCOPE: ClassVar[str] = 'https://database.windows.net/.default'

    def make_creator(self, adapter: DriverAdapter, **kwargs: Any) -> DBAPICreator:
        creds_provider = kwargs.get('creds_provider')
        if not creds_provider:
            raise KeyError('Creds provider is not given.')
        
        def _creator():
            credentials = creds_provider.creds(scope=AzureIamAsqlStrategy.SCOPE)
            token_bytes = make_token_bytes(credentials)
            return adapter.connect(
                host=self.profile.host,
                port=self.profile.port, 
                database=self.profile.database,
                ca_path=resolve_ca_bundle(),
                attrs_before={
                    AzureIamAsqlStrategy.ACCESS_TOKEN_ATTR: token_bytes
                }
            )
        return _creator
    
    def pool_settings(self) -> Dict[str, Any]:
        return {
            'pool_pre_ping': True, 
            'pool_recycle': 3000
        }
