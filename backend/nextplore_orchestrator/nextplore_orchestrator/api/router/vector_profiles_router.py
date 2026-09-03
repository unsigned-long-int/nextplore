import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from svc_vector_contracts.models import TableProfile

from nextplore_orchestrator.api.dependencies.authentication import get_active_user
from nextplore_orchestrator.api.dependencies.microservices import get_vector_client
from nextplore_orchestrator.clients.vector import VectorGetProfilesRemoteError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/nextplore-orchestrator", tags=["VectorProfiles"])


@router.get(
    "/datastores/{datastore_id}/vectors/profiles", response_model=list[TableProfile]
)
async def get_vector_profiles(
    datastore_id: UUID,
    user_identity=Depends(get_active_user),
    vector_client=Depends(get_vector_client),
) -> list[TableProfile]:
    org_id = getattr(user_identity, "organization_id", None)
    user_id = getattr(user_identity, "user_id", None)
    try:
        vector_profiles = await vector_client.get_profiles(
            organization_id=org_id, user_id=user_id, datastore_id=datastore_id
        )
        return vector_profiles

    except VectorGetProfilesRemoteError as e:
        logger.error(
            "Vector get profiles failed (remote)",
            extra={"org_id": str(org_id), "user_id": str(user_id)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY, detail={"message": str(e)}
        )
    except Exception as e:
        logger.error(
            "Vector get profiles failed (unexpected)",
            extra={"org_id": str(org_id), "user_id": str(user_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"Unexpected error: {e!s}"},
        )
