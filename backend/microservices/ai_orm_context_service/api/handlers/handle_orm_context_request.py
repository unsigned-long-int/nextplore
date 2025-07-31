from shared.contracts.ai_orm_context_service import (
    ORMContextResponse,
    ORMContextRequest
)
from services.orchestrator import AIORMRequestService
from services.context_providers.provider_factory import dispatch_context_provider
from shared.identity_service.user_identity import UserIdentity


async def handle_orm_context_request(orm_context_request: ORMContextRequest) -> ORMContextResponse:
    context_provider = dispatch_context_provider(orm_context_request.model_id)
    ai_orm_request_service = AIORMRequestService(context_provider)
    orm_context = await ai_orm_request_service.retrieve_orm_context(orm_context_request)
    return ORMContextResponse(
        integration=orm_context.integration,
        schema_name=orm_context.schema_name,
        class_name=orm_context.class_name,
        table_name=orm_context.table_name,
        column_names=orm_context.column_names,
        column_aggregates=orm_context.column_aggregates,
        column_filters=orm_context.column_filters
    )
