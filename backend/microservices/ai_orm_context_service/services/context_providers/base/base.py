from abc import ABC, abstractmethod

from shared.contracts.ai_orm_context_service import ORMContextRequest
from services.context_schema import ORMContext

class AIORMContextProviderBase(ABC):
    @abstractmethod
    async def retrieve_orm_context(self, orm_context_request: ORMContextRequest) -> ORMContext:
        ...
