import logging
import os
import secrets
from datetime import datetime, timedelta, timezone

from nextplore_sdk.database.backend.database_backend_connector import (
    DatabaseBackendConnector,
)
from svc_nextplore_orchestrator_contracts.models import (
    EmailVerificationStatusResponse,
    RegisterRequest,
    RegisterResponse,
)

from nextplore_orchestrator.cache.orchestrator_cache import OrchestratorCacheService
from nextplore_orchestrator.database.exceptions import (
    EmailOutboxCreateFailed,
    OnboardingRequestCreateFailed,
    OnboardingRequestGetFailed,
    OnboardingRequestUpdateFailed,
)
from nextplore_orchestrator.database.repositories import (
    AuthRepository,
    NotificationRepository,
)
from nextplore_orchestrator.domain.mappers import onboarding_request_from_dto

logger = logging.getLogger(__name__)

GENERIC_REGISTER_RESPONSE = "If this email address is eligible, we’ve sent a verification link. Please check your inbox."


class InvalidVerificationToken(Exception):
    pass


class OnboardingService:
    def __init__(
        self,
        db_connector: DatabaseBackendConnector,
        cache_service: OrchestratorCacheService,
    ) -> None:
        self._db = db_connector
        self._cache_service = cache_service
        self._app_url = os.getenv("NEXTPLORE_APP_URL", "http://localhost:5173")
        self._admin = os.getenv("NEXTPLORE_ADMIN_EMAIL", "admin@nextplore.co")

    async def create_onboarding_request(
        self, payload: RegisterRequest
    ) -> RegisterResponse:
        onboarding_id = None

        email_domain = str(payload.contact_email).split("@")[1].lower()
        cached = await self._cache_service.get_onboarding_response(email_domain)

        if cached:
            return cached

        req = onboarding_request_from_dto(payload)
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        url = f"{self._app_url}/register/verify?token={token}"

        try:
            async with self._db.session_scope() as scoped_session:
                auth_repo = AuthRepository(scoped_session)
                notification_repo = NotificationRepository(scoped_session)

                existing = await auth_repo.get_onboarding_request_by_domain(
                    email_domain
                )
                if existing:
                    return RegisterResponse(message=GENERIC_REGISTER_RESPONSE)

                outbox_id = await notification_repo.create_email_outbox(
                    recipient=str(payload.contact_email),
                    subject="Verify your Nextplore registration",
                    html=f"""
                        <h2>Welcome to Nextplore</h2>
                        <p>Thanks for registering <strong>{payload.company_name}</strong>.</p>
                        <p>Please verify your email address to complete your request:</p>
                        <p><a href="{url}" style="
                            background:#1976d2;color:#fff;padding:12px 24px;
                            border-radius:6px;text-decoration:none;display:inline-block
                        ">Verify email address</a></p>
                        <p>This link expires in 24 hours.</p>
                        <p style="color:#888;font-size:12px">
                            If you did not request access to Nextplore, ignore this email.
                        </p>
                    """,
                )

                _ = await notification_repo.create_email_outbox(
                    recipient=self._admin,
                    subject=f"New Nextplore access request: {payload.company_name}",
                    html=f"""
                                <h2>New access request</h2>
                                <table style="border-collapse:collapse">
                                    <tr><td style="padding:4px 12px 4px 0"><strong>Company</strong></td>
                                        <td>{payload.company_name}</td></tr>
                                    <tr><td style="padding:4px 12px 4px 0"><strong>Email</strong></td>
                                        <td>{payload.contact_email}</td></tr>
                                    <tr><td style="padding:4px 12px 4px 0"><strong>Domain</strong></td>
                                        <td>{email_domain}</td></tr>
                                    <tr><td style="padding:4px 12px 4px 0"><strong>Plan</strong></td>
                                        <td>{payload.plan}</td></tr>
                                </table>
                                <p>Review access in database</p>
                            """,
                )
                onboarding_id = await auth_repo.create_onboarding_request(
                    req=req,
                    outbox_mail_id=outbox_id,
                    token=token,
                    expires_at=expires_at,
                )
            register_response = RegisterResponse(message=GENERIC_REGISTER_RESPONSE)
            await self._cache_service.set_onboarding_response(
                response=register_response, email_domain=email_domain
            )
            return register_response

        except (
            OnboardingRequestGetFailed,
            OnboardingRequestCreateFailed,
            EmailOutboxCreateFailed,
        ) as e:
            logger.error(
                "Create onboarding request failed due to database dependency.",
                extra={
                    "email_domain": email_domain,
                    "onboarding_id": onboarding_id if onboarding_id else None,
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during create_onboarding_request.",
                extra={
                    "email_domain": email_domain,
                    "onboarding_id": onboarding_id if onboarding_id else None,
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            raise

    async def verify_email(self, token: str) -> EmailVerificationStatusResponse:
        request = None
        try:
            async with self._db.session_scope() as session:
                auth_repo = AuthRepository(session)
                notification_repo = NotificationRepository(session)
                request = await auth_repo.get_onboarding_request_by_verification_token(
                    token
                )

                if not request:
                    logger.error(f"Invalid verification token sent: {token}")
                    raise InvalidVerificationToken(
                        "Invalid or expired verification token"
                    )

                if request.email_verified:
                    return EmailVerificationStatusResponse(status="already verified")

                await auth_repo.verify_email(request.id)
                await notification_repo.create_email_outbox(
                    recipient=self._admin,
                    subject=f"New Nextplore access request: {request.company_name}",
                    html=f"""
                        <h2>Email has been successfully verified.</h2>
                        <table style="border-collapse:collapse">
                            <tr><td style="padding:4px 12px 4px 0"><strong>Company</strong></td>
                                <td>{request.company_name}</td></tr>
                            <tr><td style="padding:4px 12px 4px 0"><strong>Email</strong></td>
                                <td>{request.contact_email}</td></tr>
                            <tr><td style="padding:4px 12px 4px 0"><strong>Domain</strong></td>
                                <td>{request.email_domain}</td></tr>
                            <tr><td style="padding:4px 12px 4px 0"><strong>Plan</strong></td>
                                <td>{request.plan}</td></tr>
                        </table>
                    """,
                )
                return EmailVerificationStatusResponse(status="verified")
        except OnboardingRequestUpdateFailed as e:
            logger.error(
                "Email verification for onboarding request failed due to database dependency.",
                extra={
                    "email_domain": request.email_domain if request else None,
                    "onboarding_id": request.id if request else None,
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during email verification.",
                extra={
                    "email_domain": request.email_domain if request else None,
                    "onboarding_id": request.id if request else None,
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            raise
