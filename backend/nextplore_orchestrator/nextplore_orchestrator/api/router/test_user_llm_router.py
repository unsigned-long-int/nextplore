import logging

from fastapi import APIRouter, Depends, HTTPException, status
from svc_integration_contracts.models import UserLlmCreateRequest

from nextplore_orchestrator.api.dependencies.authentication import get_active_user
from nextplore_orchestrator.api.dependencies.microservices import (
    get_llm_inference_client,
)
from nextplore_orchestrator.clients.llm_inference import ModelResponseRemoteError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/nextplore-orchestrator", tags=["LlmTest"])


@router.post("/llm-inference/test", status_code=status.HTTP_204_NO_CONTENT)
async def test_user_llm(
    llm_create_request: UserLlmCreateRequest,
    user_identity=Depends(get_active_user),
    llm_inference_client=Depends(get_llm_inference_client),
) -> None:
    org_id = getattr(user_identity, "organization_id", None)
    user_id = getattr(user_identity, "user_id", None)

    try:
        await llm_inference_client.test_user_llm(
            organization_id=org_id, user_id=user_id, payload=llm_create_request
        )
    except ModelResponseRemoteError as e:
        logger.error(
            "User llm test failed (remote)",
            extra={"org_id": str(org_id), "user_id": str(user_id)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY, detail={"message": str(e)}
        )
    except Exception as e:
        logger.error(
            "User llm test failed (unexpected)",
            extra={"org_id": str(org_id), "user_id": str(user_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"Unexpected error: {e!s}"},
        )
