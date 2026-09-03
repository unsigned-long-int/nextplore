import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from svc_nextplore_orchestrator_contracts.models import EmailVerificationStatusResponse

from nextplore_orchestrator.api.dependencies.onboarding import get_onboarding_service
from nextplore_orchestrator.api.limiter import limiter
from nextplore_orchestrator.database.exceptions import OnboardingRequestUpdateFailed
from nextplore_orchestrator.services.onboarding import OnboardingService

router = APIRouter(prefix="/v1/nextplore-orchestrator", tags=["EmailTokenVerification"])

logger = logging.getLogger(__name__)


@router.get(
    "/organizations/register/verify", response_model=EmailVerificationStatusResponse
)
@limiter.limit("5/minute;20/hour")
async def verify_email_token(
    request: Request,
    token: str,
    onboarding_service: OnboardingService = Depends(get_onboarding_service),
) -> EmailVerificationStatusResponse | None:
    try:
        response = await onboarding_service.verify_email(token)
        return response
    except OnboardingRequestUpdateFailed as e:
        logger.error(
            f"Email verification failed with DB error: {e!s}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={"message": f"Database error: {e!s}"},
        )
    except Exception as e:
        logger.error(f"Unexpected verification email error: {e!s}.", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"Unexpected error while verifying email: {e!s}"},
        )
