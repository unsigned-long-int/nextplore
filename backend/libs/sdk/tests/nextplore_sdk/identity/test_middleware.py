import os
import secrets
import unittest
from unittest.mock import patch
from uuid import uuid4

import httpx
from nextplore_sdk.identity.context import (
    UserIdentityContextError,
    get_current_identity,
    identity_context,
)
from nextplore_sdk.identity.middleware import IdentityMiddleware
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

VALID_TOKEN = "t" * 48


async def whoami(request):
    identity = get_current_identity()
    return JSONResponse(
        {
            "user_id": str(identity.user_id),
            "organization_id": str(identity.organization_id),
        }
    )


async def health(request):
    return JSONResponse({"status": "ok"})


async def unbound(request):
    try:
        get_current_identity()
    except UserIdentityContextError:
        return JSONResponse({"bound": False})
    return JSONResponse({"bound": True})


class IdentityMiddlewareTestBase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        patcher = patch.dict(
            os.environ, {"INTERNAL_SERVICE_TOKEN": VALID_TOKEN}, clear=False
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        token = identity_context.set(None)
        self.addCleanup(identity_context.reset, token)

        self.app = Starlette(
            routes=[
                Route("/whoami", whoami),
                Route("/health", health),
                Route("/unbound", unbound),
            ],
            middleware=[],
        )
        self.app.add_middleware(IdentityMiddleware)

        self.organization_id = uuid4()
        self.user_id = uuid4()

    def valid_headers(self, **overrides) -> dict[str, str]:
        headers = {
            "x-internal-token": VALID_TOKEN,
            "x-user-id": str(self.user_id),
            "x-org-id": str(self.organization_id),
        }
        headers.update(overrides)
        return headers

    async def get(self, path: str, headers: dict[str, str] | None = None):
        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            return await client.get(path, headers=headers or {})


class TestServiceAuthentication(IdentityMiddlewareTestBase):
    async def test_rejects_request_with_no_internal_token(self):
        headers = self.valid_headers()
        del headers["x-internal-token"]

        response = await self.get("/whoami", headers)

        self.assertEqual(response.status_code, 401)

    async def test_rejects_wrong_internal_token(self):
        response = await self.get(
            "/whoami", self.valid_headers(**{"x-internal-token": "w" * 48})
        )

        self.assertEqual(response.status_code, 401)

    async def test_rejects_empty_internal_token(self):
        response = await self.get(
            "/whoami", self.valid_headers(**{"x-internal-token": ""})
        )

        self.assertEqual(response.status_code, 401)

    async def test_rejects_token_that_is_a_prefix_of_the_real_one(self):
        """Guards against a comparison that stops at the first difference."""
        response = await self.get(
            "/whoami", self.valid_headers(**{"x-internal-token": VALID_TOKEN[:-1]})
        )

        self.assertEqual(response.status_code, 401)

    async def test_accepts_the_correct_token(self):
        response = await self.get("/whoami", self.valid_headers())

        self.assertEqual(response.status_code, 200)

    async def test_rejection_body_reveals_nothing(self):
        response = await self.get(
            "/whoami", self.valid_headers(**{"x-internal-token": "nope"})
        )

        self.assertEqual(response.json(), {"detail": "Unauthorized"})


class TestIdentityHeaders(IdentityMiddlewareTestBase):
    async def test_binds_identity_from_headers(self):
        response = await self.get("/whoami", self.valid_headers())

        self.assertEqual(
            response.json(),
            {
                "user_id": str(self.user_id),
                "organization_id": str(self.organization_id),
            },
        )

    async def test_rejects_missing_user_id(self):
        headers = self.valid_headers()
        del headers["x-user-id"]

        response = await self.get("/whoami", headers)

        self.assertEqual(response.status_code, 401)

    async def test_rejects_missing_org_id(self):
        headers = self.valid_headers()
        del headers["x-org-id"]

        response = await self.get("/whoami", headers)

        self.assertEqual(response.status_code, 401)

    async def test_rejects_empty_user_id(self):
        response = await self.get("/whoami", self.valid_headers(**{"x-user-id": ""}))

        self.assertEqual(response.status_code, 401)

    async def test_malformed_user_id_returns_401_not_500(self):
        response = await self.get(
            "/whoami", self.valid_headers(**{"x-user-id": "not-a-uuid"})
        )

        self.assertEqual(response.status_code, 401)

    async def test_malformed_org_id_returns_401_not_500(self):
        response = await self.get(
            "/whoami", self.valid_headers(**{"x-org-id": "not-a-uuid"})
        )

        self.assertEqual(response.status_code, 401)

    async def test_header_names_are_case_insensitive(self):
        response = await self.get(
            "/whoami",
            {
                "X-Internal-Token": VALID_TOKEN,
                "X-User-Id": str(self.user_id),
                "X-Org-Id": str(self.organization_id),
            },
        )

        self.assertEqual(response.status_code, 200)


class TestIdentityScoping(IdentityMiddlewareTestBase):
    async def test_identity_is_not_visible_after_the_request(self):
        await self.get("/whoami", self.valid_headers())

        with self.assertRaises(UserIdentityContextError):
            get_current_identity()

    async def test_consecutive_requests_do_not_share_an_identity(self):
        first = await self.get("/whoami", self.valid_headers())

        other_user, other_org = uuid4(), uuid4()
        second = await self.get(
            "/whoami",
            {
                "x-internal-token": VALID_TOKEN,
                "x-user-id": str(other_user),
                "x-org-id": str(other_org),
            },
        )

        self.assertEqual(first.json()["user_id"], str(self.user_id))
        self.assertEqual(second.json()["user_id"], str(other_user))

    async def test_rejected_request_leaves_no_identity_behind(self):
        await self.get("/whoami", self.valid_headers(**{"x-internal-token": "nope"}))

        with self.assertRaises(UserIdentityContextError):
            get_current_identity()


class TestExemptPaths(IdentityMiddlewareTestBase):
    async def test_health_is_reachable_without_any_headers(self):
        response = await self.get("/health")

        self.assertEqual(response.status_code, 200)

    async def test_exempt_path_leaves_the_identity_unbound(self):
        app = Starlette(routes=[Route("/health", unbound)])
        app.add_middleware(IdentityMiddleware)
        self.app = app

        response = await self.get("/health")

        self.assertEqual(response.json(), {"bound": False})

    async def test_non_exempt_path_still_requires_the_token(self):
        response = await self.get("/whoami")

        self.assertEqual(response.status_code, 401)

    async def test_custom_exempt_paths_are_honoured(self):
        app = Starlette(routes=[Route("/metrics", health)])
        app.add_middleware(IdentityMiddleware, exempt_paths=frozenset({"/metrics"}))
        self.app = app

        response = await self.get("/metrics")

        self.assertEqual(response.status_code, 200)


class TestConfiguration(unittest.TestCase):
    def test_missing_token_env_var_fails_at_startup(self):
        app = Starlette(routes=[])

        with patch.dict(os.environ, {}, clear=True), self.assertRaises(KeyError):
            IdentityMiddleware(app)

    def test_short_token_is_rejected(self):
        app = Starlette(routes=[])

        with patch.dict(os.environ, {"INTERNAL_SERVICE_TOKEN": "short"}):
            with self.assertRaises(RuntimeError) as ctx:
                IdentityMiddleware(app)

        self.assertIn("32", str(ctx.exception))

    def test_a_generated_token_is_long_enough(self):
        app = Starlette(routes=[])
        generated = secrets.token_urlsafe(48)

        with patch.dict(os.environ, {"INTERNAL_SERVICE_TOKEN": generated}):
            IdentityMiddleware(app)
