import unittest
import uuid
from unittest.mock import AsyncMock, patch

from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Scope, Receive

from api.middleware import IdentityMiddleware
from nextplore_shared.identity_service.identity_model.user_identity import UserIdentity


class TestIdentityMiddleware(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = AsyncMock()
        self.middleware = IdentityMiddleware(self.app)

    def make_request(self, headers: dict):
        scope: Scope = {
            'type': 'http',
            'method': 'GET',
            'path': '/',
            'headers': [(k.encode(), v.encode()) for k, v in headers.items()],
        }

        receive: Receive = AsyncMock()
        return Request(scope, receive=receive)

    @patch('api.middleware.identity.set_current_identity')
    async def test_identity_set_when_headers_present(self, mock_set_identity):
        user_id = str(uuid.uuid4())
        org_id = str(uuid.uuid4())

        request = self.make_request({
            'x-user-id': user_id,
            'x-org-id': org_id
        })

        response = Response('OK')
        self.app.return_value = response

        result = await self.middleware.dispatch(request, self.app)

        self.assertEqual(result, response)
        mock_set_identity.assert_called_once()
        
        actual_identity = mock_set_identity.call_args.args[0]
        self.assertIsInstance(actual_identity, UserIdentity)
        self.assertEqual(actual_identity.user_id, uuid.UUID(user_id))
        self.assertEqual(actual_identity.organization_id, uuid.UUID(org_id))

    @patch('api.middleware.identity.set_current_identity')
    async def test_identity_not_set_when_headers_missing(self, mock_set_identity):
        request = self.make_request({})

        response = Response('OK')
        self.app.return_value = response

        result = await self.middleware.dispatch(request, self.app)

        self.assertEqual(result, response)
        mock_set_identity.assert_not_called()

