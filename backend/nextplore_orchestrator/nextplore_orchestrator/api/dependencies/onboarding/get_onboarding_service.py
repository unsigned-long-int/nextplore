from fastapi import Request

from nextplore_orchestrator.services.onboarding import OnboardingService


def get_onboarding_service(request: Request) -> OnboardingService:
    return request.app.state.onboarding_service