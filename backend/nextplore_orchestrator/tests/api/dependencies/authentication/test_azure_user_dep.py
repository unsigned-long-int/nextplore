import unittest
from unittest.mock import AsyncMock, MagicMock

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from nextplore_orchestrator.api.dependencies.authentication.azure_user_dep import (
    get_azure_user,
)


def make_request(token_verifier) -> MagicMock:
    request = MagicMock()
    request.app.state.token_verifier = token_verifier
    return request


def make_creds(token: str = "a-jwt-token") -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


class GetAzureUserTestBase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.token_verifier = AsyncMock()
        self.request = make_request(self.token_verifier)
        self.creds = make_creds()


class TestSuccess(GetAzureUserTestBase):
    async def test_returns_the_claims(self):
        claims = {"tid": "tenant-abc", "oid": "user-abc"}
        self.token_verifier.verify_token.return_value = claims

        result = await get_azure_user(request=self.request, creds=self.creds)

        self.assertEqual(result, claims)

    async def test_passes_the_bearer_token_to_the_verifier(self):
        self.token_verifier.verify_token.return_value = {}
        creds = make_creds(token="specific-token-value")

        await get_azure_user(request=self.request, creds=creds)

        self.token_verifier.verify_token.assert_awaited_once_with(
            "specific-token-value"
        )

    async def test_uses_the_verifier_from_app_state(self):
        other_verifier = AsyncMock()
        other_verifier.verify_token.return_value = {"tid": "from-other-verifier"}
        request = make_request(other_verifier)

        result = await get_azure_user(request=request, creds=self.creds)

        self.assertEqual(result["tid"], "from-other-verifier")
        self.token_verifier.verify_token.assert_not_awaited()


class TestValueErrorIsTranslated(GetAzureUserTestBase):
    async def test_value_error_becomes_a_401(self):
        self.token_verifier.verify_token.side_effect = ValueError("bad token")

        with self.assertRaises(HTTPException) as ctx:
            await get_azure_user(request=self.request, creds=self.creds)

        self.assertEqual(ctx.exception.status_code, 401)

    async def test_value_error_detail_does_not_leak_the_original_message(self):
        self.token_verifier.verify_token.side_effect = ValueError(
            "unexpected token content: <script>alert(1)</script>"
        )

        with self.assertRaises(HTTPException) as ctx:
            await get_azure_user(request=self.request, creds=self.creds)

        self.assertEqual(ctx.exception.detail, "Invalid or expired token")
        self.assertNotIn("script", str(ctx.exception.detail))


class TestOtherExceptionsAreNotCaught(GetAzureUserTestBase):
    async def test_http_exception_from_the_verifier_propagates_unchanged(self):
        original = HTTPException(status_code=401, detail="Invalid issuer")
        self.token_verifier.verify_token.side_effect = original

        with self.assertRaises(HTTPException) as ctx:
            await get_azure_user(request=self.request, creds=self.creds)

        self.assertIs(ctx.exception, original)
        self.assertEqual(ctx.exception.detail, "Invalid issuer")

    async def test_unrelated_exception_is_not_translated_to_401(self):
        self.token_verifier.verify_token.side_effect = RuntimeError(
            "JWKS endpoint unreachable"
        )

        with self.assertRaises(RuntimeError):
            await get_azure_user(request=self.request, creds=self.creds)
