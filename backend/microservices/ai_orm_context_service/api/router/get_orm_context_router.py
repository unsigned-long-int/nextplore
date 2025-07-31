from fastapi import APIRouter

from shared.contracts.ai_orm_context_service import ORMContextResponse, ORMContextRequest
from api.handlers import handle_orm_context_request


router = APIRouter(prefix='/v1/ai-orm', tags=['AIORMContext'])

@router.post('/get-context', response_model=ORMContextResponse)
async def get_orm_context(payload: ORMContextRequest) -> ORMContextResponse:
    response = await handle_orm_context_request(
        orm_context_request=payload
    )
    return response
