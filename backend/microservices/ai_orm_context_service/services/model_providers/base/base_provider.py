from abc import ABC, abstractmethod

from nextplore_shared.contracts.ai_orm_context_service.orm_context_request import ORMContextRequest
from services.orm_context_builder.orm_context_model import ORMContext


class BaseProvider(ABC):
    @abstractmethod
    async def retrieve_model_response(self, orm_context_request: ORMContextRequest) -> ORMContext:
        ...
