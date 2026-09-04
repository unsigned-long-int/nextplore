import base64
import time
import unittest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from jose import jwt
from nextplore_orchestrator.api.dependencies.authentication.auth import TokenVerifier

MODULE = "nextplore_orchestrator.api.dependencies.authentication.auth"

AUDIENCE = "test-audience"
AUTHORITY = "https://login.microsoftonline.com"
TENANT_ID = "tenant-" + str(uuid4())
KID = "test-kid"


def b64url(n: int, length: int) -> str:
    return base64.urlsafe_b64encode(n.to_bytes(length, "big")).rstrip(b"=").decode()


class RsaFixture:
    def __init__(self):
        self.private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048
        )
        numbers = self.private_key.public_key().public_numbers()
        self.jwk = {
            "kty": "RSA",
            "kid": KID,
            "use": "sig",
            "alg": "RS256",
            "n": b64url(numbers.n, 256),
            "e": b64url(numbers.e, 3),
        }

    @property
    def private_pem(self) -> bytes:
        from cryptography.hazmat.primitives import serialization

        return self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

    def jwks(self, kid: str | None = None) -> dict:
        key = dict(self.jwk)
        if kid is not None:
            key["kid"] = kid
        return {"keys": [key]}

    def sign(self, claims: dict, kid: str = KID, algorithm: str = "RS256") -> str:
        return jwt.encode(
            claims, self.private_pem, algorithm=algorithm, headers={"kid": kid}
        )


RSA = RsaFixture()


def make_claims(**overrides) -> dict:
    now = int(time.time())
    claims = {
        "aud": AUDIENCE,
        "iss": f"{AUTHORITY}/{TENANT_ID}/v2.0",
        "tid": TENANT_ID,
        "iat": now,
        "exp": now + 3600,
    }
    claims.update(overrides)
    return claims


class TokenVerifierTestBase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        patcher = patch.multiple(
            MODULE,
            JWKS_URL="https://example.com/.well-known/jwks.json",
            JWT_AUDIENCE=AUDIENCE,
            AZURE_AUTHORITY=AUTHORITY,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        self.jwks_fetcher = AsyncMock()
        self.jwks_fetcher.get_jwks.return_value = RSA.jwks()

        self.verifier = TokenVerifier(jwks_fetcher=self.jwks_fetcher)

    def token(self, **claim_overrides) -> str:
        return RSA.sign(make_claims(**claim_overrides))

    async def assert_rejected(
        self, token: str, detail: str | None = None
    ) -> HTTPException:
        with self.assertRaises(HTTPException) as ctx:
            await self.verifier.verify_token(token)

        self.assertEqual(ctx.exception.status_code, 401)
        if detail is not None:
            self.assertEqual(ctx.exception.detail, detail)
        return ctx.exception


class TestValidToken(TokenVerifierTestBase):
    async def test_returns_the_claims(self):
        result = await self.verifier.verify_token(self.token())

        self.assertEqual(result["tid"], TENANT_ID)
        self.assertEqual(result["aud"], AUDIENCE)

    async def test_fetches_jwks_for_the_tokens_kid(self):
        await self.verifier.verify_token(self.token())

        self.jwks_fetcher.get_jwks.assert_awaited_once_with(
            jwks_url="https://example.com/.well-known/jwks.json",
            expected_kid=KID,
        )

    async def test_extra_claims_are_returned_unmodified(self):
        result = await self.verifier.verify_token(self.token(oid="user-object-id"))

        self.assertEqual(result["oid"], "user-object-id")


class TestMalformedToken(TokenVerifierTestBase):
    async def test_garbage_string_is_rejected(self):
        await self.assert_rejected("not-a-jwt-at-all", "Malformed token header")

    async def test_empty_string_is_rejected(self):
        await self.assert_rejected("", "Malformed token header")

    async def test_does_not_call_jwks_fetcher_for_a_malformed_token(self):
        with self.assertRaises(HTTPException):
            await self.verifier.verify_token("garbage")

        self.jwks_fetcher.get_jwks.assert_not_awaited()

    async def test_missing_kid_is_rejected(self):
        token = jwt.encode(make_claims(), RSA.private_pem, algorithm="RS256")
        # signed with no `kid` header at all

        await self.assert_rejected(token, "Token missing kid claim")

    async def test_does_not_call_jwks_fetcher_when_kid_is_missing(self):
        token = jwt.encode(make_claims(), RSA.private_pem, algorithm="RS256")

        with self.assertRaises(HTTPException):
            await self.verifier.verify_token(token)

        self.jwks_fetcher.get_jwks.assert_not_awaited()


class TestUnknownKey(TokenVerifierTestBase):
    async def test_kid_absent_from_jwks_is_rejected(self):
        self.jwks_fetcher.get_jwks.return_value = RSA.jwks(kid="a-different-kid")

        await self.assert_rejected(self.token(), "Unknown key ID")

    async def test_empty_jwks_is_rejected(self):
        self.jwks_fetcher.get_jwks.return_value = {"keys": []}

        await self.assert_rejected(self.token(), "Unknown key ID")

    async def test_jwks_missing_the_keys_field_is_rejected(self):
        self.jwks_fetcher.get_jwks.return_value = {}

        await self.assert_rejected(self.token(), "Unknown key ID")


class TestSignature(TokenVerifierTestBase):
    async def test_token_signed_by_a_different_key_is_rejected(self):
        other_key = RsaFixture()
        forged = other_key.sign(make_claims())

        await self.assert_rejected(forged, "Token verification failed")

    async def test_tampered_payload_is_rejected(self):
        token = self.token()
        header, _, signature = token.split(".")
        tampered_payload = (
            base64.urlsafe_b64encode(
                b'{"tid":"attacker-tenant","aud":"' + AUDIENCE.encode() + b'"}'
            )
            .rstrip(b"=")
            .decode()
        )
        tampered = f"{header}.{tampered_payload}.{signature}"

        await self.assert_rejected(tampered, "Token verification failed")

    async def test_none_algorithm_is_rejected(self):
        header = base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').rstrip(b"=")
        payload = base64.urlsafe_b64encode(
            f'{{"tid":"{TENANT_ID}","aud":"{AUDIENCE}"}}'.encode()
        ).rstrip(b"=")
        forged = header.decode() + "." + payload.decode() + "."

        await self.assert_rejected(forged)


class TestClaimValidation(TokenVerifierTestBase):
    async def test_expired_token_is_rejected(self):
        expired = self.token(exp=int(time.time()) - 3600, iat=int(time.time()) - 7200)

        await self.assert_rejected(expired, "Token verification failed")

    async def test_token_within_the_leeway_window_is_accepted(self):
        barely_expired = self.token(
            exp=int(time.time()) - 30, iat=int(time.time()) - 3600
        )

        result = await self.verifier.verify_token(barely_expired)

        self.assertEqual(result["tid"], TENANT_ID)

    async def test_token_well_past_the_leeway_is_rejected(self):
        expired = self.token(exp=int(time.time()) - 90, iat=int(time.time()) - 3600)

        await self.assert_rejected(expired)

    async def test_wrong_audience_is_rejected(self):
        wrong_aud = self.token(aud="a-different-audience")

        await self.assert_rejected(wrong_aud, "Token verification failed")

    async def test_missing_tid_is_rejected(self):
        token = RSA.sign({k: v for k, v in make_claims().items() if k != "tid"})

        await self.assert_rejected(token, "Missing required claims")

    async def test_missing_iss_is_rejected(self):
        token = RSA.sign({k: v for k, v in make_claims().items() if k != "iss"})

        await self.assert_rejected(token, "Missing required claims")

    async def test_empty_tid_is_rejected(self):
        token = self.token(tid="")

        await self.assert_rejected(token, "Missing required claims")

    async def test_does_not_reach_issuer_check_when_tid_is_missing(self):
        token = RSA.sign({k: v for k, v in make_claims().items() if k != "tid"})

        exc = await self.assert_rejected(token)

        self.assertEqual(exc.detail, "Missing required claims")


class TestIssuerValidation(TokenVerifierTestBase):
    async def test_issuer_from_a_different_tenant_is_rejected(self):
        wrong_tenant_iss = self.token(iss=f"{AUTHORITY}/{uuid4()}/v2.0")

        await self.assert_rejected(wrong_tenant_iss, "Invalid issuer")

    async def test_issuer_from_a_different_authority_is_rejected(self):
        wrong_authority = self.token(iss=f"https://evil.example/{TENANT_ID}/v2.0")

        await self.assert_rejected(wrong_authority, "Invalid issuer")

    async def test_issuer_missing_the_v2_suffix_is_rejected(self):
        no_suffix = self.token(iss=f"{AUTHORITY}/{TENANT_ID}")

        await self.assert_rejected(no_suffix, "Invalid issuer")

    async def test_issuer_claiming_a_tenant_that_does_not_match_tid_is_rejected(self):
        mismatched = self.token(tid=TENANT_ID, iss=f"{AUTHORITY}/{uuid4()}/v2.0")

        await self.assert_rejected(mismatched, "Invalid issuer")

    async def test_correct_issuer_for_the_tenant_is_accepted(self):
        result = await self.verifier.verify_token(self.token())

        self.assertEqual(result["iss"], f"{AUTHORITY}/{TENANT_ID}/v2.0")


class TestAlgorithmPinning(TokenVerifierTestBase):
    async def test_only_rs256_is_accepted(self):
        hs256_token = jwt.encode(make_claims(), "some-shared-secret", algorithm="HS256")

        await self.assert_rejected(hs256_token, "Token missing kid claim")

    async def test_rs256_token_with_hs256_declared_in_header_is_rejected(self):
        forged = jwt.encode(
            make_claims(), "some-shared-secret", algorithm="HS256", headers={"kid": KID}
        )

        await self.assert_rejected(forged, "Token verification failed")
