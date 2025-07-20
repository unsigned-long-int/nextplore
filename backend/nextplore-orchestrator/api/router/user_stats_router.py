from fastapi import APIRouter, Depends

from api.models import UserStats
from api.dependencies.authentication import get_active_user
from api.dependencies.microservices import get_integration_client, get_vector_client
from shared.contracts.integration_service import IntegrationStatsRequest
from shared.contracts.vector_service import VectorMetaRequest


router = APIRouter()

@router.get('', response_model=UserStats)
async def get_user_stats(
    user_identity=Depends(get_active_user),
    integration_client=Depends(get_integration_client),
    vector_client=Depends(get_vector_client)
) ->  UserStats:    
    payload = IntegrationStatsRequest(
        user_id=user_identity.user_id,
        organization_id=user_identity.organization_id
    )
    integration_stats = await integration_client.get_integration_stats(payload)

    payload = VectorMetaRequest(
        integration_ids=integration_stats.integration_ids
    )
    vector_stats = await vector_client.get_vector_stats(payload)

    return UserStats(
        integrations_number=integration_stats.integration_count, 
        vectors_number=vector_stats.vector_count
    )

    

