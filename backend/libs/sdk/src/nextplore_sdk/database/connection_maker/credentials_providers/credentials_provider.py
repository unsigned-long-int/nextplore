from abc import ABC, abstractmethod
from typing import Any

from nextplore_sdk.database.connection_maker.models.connection_profile import (
    ConnectionProfile,
)


class CredentialsProvider(ABC):
    def __init__(self, profile: ConnectionProfile) -> None:
        self.profile = profile

    @abstractmethod
    def creds(self, **kwargs: Any) -> str: ...
