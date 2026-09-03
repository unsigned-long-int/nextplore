from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from nextplore_sdk.database.connection_maker.driver_adapters.driver_adapter import (
    DriverAdapter,
)
from nextplore_sdk.database.connection_maker.models.connection_profile import (
    ConnectionProfile,
)

DBAPICreator = Callable[[], "DBAPIConnection"]


class AuthStrategy(ABC):
    def __init__(self, profile: ConnectionProfile) -> None:
        self.profile = profile

    @abstractmethod
    def make_creator(self, adapter: DriverAdapter, **kwargs: Any) -> DBAPICreator: ...

    @abstractmethod
    def pool_settings(self) -> dict[str, Any]: ...
