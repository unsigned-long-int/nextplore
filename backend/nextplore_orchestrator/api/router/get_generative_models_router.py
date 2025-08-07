from fastapi import APIRouter, Depends

from nextplore_shared.contracts.ai_orm_context_service.avilable_models_response import AvailableModelsResponse
from api.dependencies.authentication import get_active_user
from api.dependencies.microservices import get_ai_orm_context_client


router = APIRouter()

@router.get('', response_model=AvailableModelsResponse)
async def ai_query(
    user_identity=Depends(get_active_user),
    ai_orm_context_client=Depends(get_ai_orm_context_client)
) -> AvailableModelsResponse:
    response = await ai_orm_context_client.get_models()
    return response