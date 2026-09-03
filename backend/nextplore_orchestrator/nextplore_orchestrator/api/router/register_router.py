import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from svc_nextplore_orchestrator_contracts.models import (
    RegisterRequest,
    RegisterResponse,
)

from nextplore_orchestrator.api.dependencies.onboarding import get_onboarding_service
from nextplore_orchestrator.api.limiter import limiter
from nextplore_orchestrator.database.exceptions import (
    EmailOutboxCreateFailed,
    OnboardingRequestCreateFailed,
    OnboardingRequestGetFailed,
)
from nextplore_orchestrator.services.onboarding import OnboardingService

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/v1/nextplore-orchestrator", tags=["Register"])


@router.post(
    "/organizations/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("5/minute;20/hour")
async def register_organization(
    request: Request,
    register_request: RegisterRequest,
    onboarding_service: OnboardingService = Depends(get_onboarding_service),
) -> RegisterResponse | None:
    try:
        return await onboarding_service.create_onboarding_request(register_request)
    except (
        OnboardingRequestGetFailed,
        OnboardingRequestCreateFailed,
        EmailOutboxCreateFailed,
    ) as e:
        logger.error(
            f"Create onboarding request with DB error: {e!s}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={"message": f"Database error: {e!s}"},
        )
    except Exception as e:
        logger.error(
            f"Unexpected create onboarding request  error: {e!s}.", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": f"Unexpected error while creating onboarding request: {e!s}"
            },
        )
