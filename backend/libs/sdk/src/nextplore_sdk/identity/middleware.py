import os
import secrets
from uuid import UUID

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from .context import UserIdentity, current_identity

_UNAUTHORIZED = JSONResponse({"detail": "Unauthorized"}, status_code=401)


class IdentityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, exempt_paths: frozenset[str] | None = None):
        super().__init__(app)
        self._secret = os.environ["INTERNAL_SERVICE_TOKEN"]
        if len(self._secret) < 32:
            raise RuntimeError("INTERNAL_SERVICE_TOKEN must be at least 32 chars")
        self._exempt = exempt_paths or frozenset({"/health", "/ready"})

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self._exempt:
            return await call_next(request)

        presented = request.headers.get("x-internal-token", "")
        if not secrets.compare_digest(presented, self._secret):
            return _UNAUTHORIZED

        user_id = request.headers.get("x-user-id")
        org_id = request.headers.get("x-org-id")
        if not user_id or not org_id:
            return _UNAUTHORIZED

        try:
            identity = UserIdentity(
                user_id=UUID(user_id), organization_id=UUID(org_id)
            )
        except ValueError:
            return _UNAUTHORIZED

        with current_identity(identity):
            return await call_next(request)