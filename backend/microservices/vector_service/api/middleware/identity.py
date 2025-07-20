from uuid import UUID
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from shared.identity_service.user_identity import UserIdentity
from api.context.identity_context import set_current_identity


class IdentityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        user_id = request.headers.get('x-user-id')
        org_id = request.headers.get('x-org-id')

        if user_id and org_id:
            identity = UserIdentity(user_id=UUID(user_id), organization_id=UUID(org_id))
            set_current_identity(identity)

        return await call_next(request)
