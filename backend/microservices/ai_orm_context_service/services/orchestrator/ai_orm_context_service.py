from services.context_providers import AIORMContextProviderBase
from services.context_schema import ORMContext
from shared.contracts.ai_orm_context_service import ORMContextRequest


class AIORMRequestService:
    def __init__(self, strategy: AIORMContextProviderBase) -> None:
        self.strategy = strategy

    async def retrieve_orm_context(self, orm_context_request: ORMContextRequest) -> ORMContext:
        orm_context = await self.strategy.retrieve_orm_context(orm_context_request)
        return orm_context
    