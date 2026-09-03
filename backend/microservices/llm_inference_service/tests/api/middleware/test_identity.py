import uuid
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Receive, Scope

from llm_inference_service.api.context import UserIdentity
from llm_inference_service.api.middleware import IdentityMiddleware


class TestIdentity(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = AsyncMock()
        self.middleware = IdentityMiddleware(self.app)

    def make_request(self, headers: dict[str, str]):
        scope: Scope = {
            "type": "http",
            "method": "GET",
            "path": "/whatever",
            "headers": [(n.encode(), v.encode()) for n, v in headers.items()],
        }
        receive: Receive = AsyncMock()
        return Request(scope, receive)

    @patch("llm_inference_service.api.middleware.identity.set_current_identity")
    async def test_identity_set_if_headers_available(self, set_current_identity_mock):
        user_id = str(uuid.uuid4())
        organization_id = str(uuid.uuid4())

        request = self.make_request({"x-user-id": user_id, "x-org-id": organization_id})

        response = Response("OK")
        self.app.return_value = response

        result = await self.middleware.dispatch(request, self.app)

        self.assertEqual(result, response)
        set_current_identity_mock.assert_called_once()

        actual_identity = set_current_identity_mock.call_args.args[0]
        self.assertIsInstance(actual_identity, UserIdentity)
        self.assertEqual(actual_identity.user_id, uuid.UUID(user_id))
        self.assertEqual(actual_identity.organization_id, uuid.UUID(organization_id))

    @patch("llm_inference_service.api.middleware.identity.set_current_identity")
    async def test_identity_set_if_headers_not_available(
        self, set_current_identity_mock
    ):
        request = self.make_request({})
        response = Response("OK")
        self.app.return_value = response

        result = await self.middleware.dispatch(request, self.app)

        self.assertEqual(result, response)
        set_current_identity_mock.assert_not_called()
