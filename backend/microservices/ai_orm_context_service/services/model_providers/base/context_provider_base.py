from abc import ABC, abstractmethod

from nextplore_sdk.contracts.ai_orm_context_service.orm_context_request import ORMContextRequest
from services.context_service.domain_models import ORMContext


class AIORMContextProviderBase(ABC):
    def __init__(self, model_id: str) -> None:
        self.model_id = model_id

    @abstractmethod
    async def retrieve_orm_context(self, orm_context_request: ORMContextRequest) -> ORMContext:
        ...
