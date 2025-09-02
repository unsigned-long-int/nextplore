from typing import Callable, Dict, Any
from abc import ABC, abstractmethod

from connection_maker.models.connection_profile import ConnectionProfile
from connection_maker.driver_adapters.driver_adapter import DriverAdapter

DBAPICreator = Callable[[], 'DBAPIConnection']



class AuthStrategy(ABC):
    def __init__(self, profile: ConnectionProfile) -> None:
        self.profile = profile
    
    @abstractmethod
    def make_creator(self, adapter: DriverAdapter, **kwargs) -> DBAPICreator: ...

    @abstractmethod
    def pool_settings(self) -> Dict[str, Any]: ...