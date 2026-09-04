import asyncio
import time
import unittest
from unittest import mock
from unittest.mock import AsyncMock

import httpx
from fastapi import HTTPException
from nextplore_orchestrator.api.dependencies.authentication.cache_entry import (
    CacheEntry,
)
from nextplore_orchestrator.api.dependencies.authentication.jwks_fetcher import (
    JWKSFetcher,
    _coerce_jwks,
    _parse_ttl,
    _with_jitter,
)

URL = "https://login.microsoftonline.com/tenant/discovery/v2.0/keys"


def make_jwks(*kids: str) -> dict:
    return {"keys": [{"kid": kid, "kty": "RSA"} for kid in kids]}


def make_response(
    status_code: int = 200,
    json_body: dict | None = None,
    headers: dict | None = None,
    content: bytes | None = None,
) -> httpx.Response:
    request = httpx.Request("GET", URL)
    kwargs = {"status_code": status_code, "headers": headers or {}, "request": request}
    if content is not None:
        kwargs["content"] = content
    elif json_body is not None:
        kwargs["json"] = json_body
    return httpx.Response(**kwargs)


def make_entry(
    kids: tuple[str, ...] = ("kid-1",),
    expires_in: float = 600,
    etag: str | None = None,
) -> CacheEntry:
    jwks = make_jwks(*kids)
    return CacheEntry(
        jwks=jwks,
        kid_index={k["kid"]: k for k in jwks["keys"]},
        expires_at=time.time() + expires_in,
        etag=etag,
    )


class JWKSFetcherTestBase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.jwks_cache = AsyncMock()
        self.jwks_cache.get_jwks.return_value = None

        self.fetcher = JWKSFetcher(jwks_cache=self.jwks_cache, ttl=600)
        self.fetcher._client = AsyncMock(spec=httpx.AsyncClient)
        self.fetcher._client.get.return_value = make_response(
            json_body=make_jwks("kid-1")
        )

    async def asyncTearDown(self):
        await self.fetcher.aclose()


class TestInMemoryTier(JWKSFetcherTestBase):
    async def test_valid_entry_is_returned_without_any_io(self):
        entry = make_entry(kids=("kid-1",))
        self.fetcher._mem[URL] = entry

        result = await self.fetcher.get_jwks(URL, expected_kid="kid-1")

        self.assertIs(result, entry.jwks)
        self.jwks_cache.get_jwks.assert_not_awaited()
        self.fetcher._client.get.assert_not_awaited()

    async def test_no_expected_kid_accepts_any_valid_entry(self):
        entry = make_entry(kids=("some-other-kid",))
        self.fetcher._mem[URL] = entry

        result = await self.fetcher.get_jwks(URL, expected_kid=None)

        self.assertIs(result, entry.jwks)
        self.fetcher._client.get.assert_not_awaited()

    async def test_expired_entry_falls_through_to_fetch(self):
        self.fetcher._mem[URL] = make_entry(kids=("kid-1",), expires_in=-10)

        await self.fetcher.get_jwks(URL, expected_kid="kid-1")

        self.fetcher._client.get.assert_awaited_once()

    async def test_unexpired_entry_missing_the_kid_falls_through(self):
        self.fetcher._mem[URL] = make_entry(kids=("old-kid",), expires_in=600)

        await self.fetcher.get_jwks(URL, expected_kid="new-kid")

        self.fetcher._client.get.assert_awaited_once()


class TestDistributedCacheTier(JWKSFetcherTestBase):
    async def test_hit_with_matching_kid_avoids_http_fetch(self):
        self.jwks_cache.get_jwks.return_value = make_jwks("kid-1")

        result = await self.fetcher.get_jwks(URL, expected_kid="kid-1")

        self.assertEqual(result, make_jwks("kid-1"))
        self.fetcher._client.get.assert_not_awaited()

    async def test_hit_populates_the_in_memory_tier(self):
        self.jwks_cache.get_jwks.return_value = make_jwks("kid-1")

        await self.fetcher.get_jwks(URL, expected_kid="kid-1")

        self.assertIn(URL, self.fetcher._mem)
        self.assertIn("kid-1", self.fetcher._mem[URL].kid_index)

    async def test_hit_missing_the_kid_still_falls_through_to_fetch(self):
        self.jwks_cache.get_jwks.return_value = make_jwks("old-kid")

        await self.fetcher.get_jwks(URL, expected_kid="new-kid")

        self.fetcher._client.get.assert_awaited_once()

    async def test_string_encoded_jwks_is_parsed(self):
        import json

        self.jwks_cache.get_jwks.return_value = json.dumps(make_jwks("kid-1"))

        result = await self.fetcher.get_jwks(URL, expected_kid="kid-1")

        self.assertEqual(result, make_jwks("kid-1"))
        self.fetcher._client.get.assert_not_awaited()

    async def test_read_failure_is_logged_and_falls_through_to_fetch(self):
        self.jwks_cache.get_jwks.side_effect = ConnectionError("redis down")

        result = await self.fetcher.get_jwks(URL, expected_kid="kid-1")

        self.assertEqual(result, make_jwks("kid-1"))
        self.fetcher._client.get.assert_awaited_once()

    async def test_malformed_cached_value_falls_through_to_fetch(self):
        self.jwks_cache.get_jwks.return_value = {"not_keys": []}

        result = await self.fetcher.get_jwks(URL, expected_kid="kid-1")

        self.assertEqual(result, make_jwks("kid-1"))
        self.fetcher._client.get.assert_awaited_once()

    async def test_miss_falls_through_to_fetch(self):
        self.jwks_cache.get_jwks.return_value = None

        await self.fetcher.get_jwks(URL, expected_kid="kid-1")

        self.fetcher._client.get.assert_awaited_once()


class TestHttpFetch(JWKSFetcherTestBase):
    async def test_successful_fetch_returns_the_jwks(self):
        self.fetcher._client.get.return_value = make_response(
            json_body=make_jwks("kid-1", "kid-2")
        )

        result = await self.fetcher.get_jwks(URL, expected_kid="kid-1")

        self.assertEqual(result, make_jwks("kid-1", "kid-2"))

    async def test_successful_fetch_populates_in_memory_and_distributed_cache(self):
        self.fetcher._client.get.return_value = make_response(
            json_body=make_jwks("kid-1"), headers={"Cache-Control": "max-age=300"}
        )

        await self.fetcher.get_jwks(URL, expected_kid="kid-1")

        self.assertIn(URL, self.fetcher._mem)
        self.jwks_cache.set_jwks.assert_awaited_once()
        call = self.jwks_cache.set_jwks.await_args
        self.assertEqual(call.args[0], URL)
        self.assertEqual(call.kwargs["data"], make_jwks("kid-1"))

    async def test_ttl_is_read_from_cache_control_header(self):
        self.fetcher._client.get.return_value = make_response(
            json_body=make_jwks("kid-1"), headers={"Cache-Control": "max-age=120"}
        )

        with mock.patch(
            "nextplore_orchestrator.api.dependencies.authentication.jwks_fetcher._with_jitter",
            side_effect=lambda ttl: ttl,
        ):
            await self.fetcher.get_jwks(URL, expected_kid="kid-1")

        self.assertEqual(self.jwks_cache.set_jwks.await_args.kwargs["ttl"], 120)

    async def test_ttl_below_minimum_is_clamped(self):
        self.fetcher._client.get.return_value = make_response(
            json_body=make_jwks("kid-1"), headers={"Cache-Control": "max-age=5"}
        )

        with mock.patch(
            "nextplore_orchestrator.api.dependencies.authentication.jwks_fetcher._with_jitter",
            side_effect=lambda ttl: ttl,
        ):
            await self.fetcher.get_jwks(URL, expected_kid="kid-1")

        self.assertEqual(self.jwks_cache.set_jwks.await_args.kwargs["ttl"], 60)

    async def test_missing_cache_control_falls_back_to_default_ttl(self):
        self.fetcher._client.get.return_value = make_response(
            json_body=make_jwks("kid-1"), headers={}
        )

        with mock.patch(
            "nextplore_orchestrator.api.dependencies.authentication.jwks_fetcher._with_jitter",
            side_effect=lambda ttl: ttl,
        ):
            await self.fetcher.get_jwks(URL, expected_kid="kid-1")

        self.assertEqual(self.jwks_cache.set_jwks.await_args.kwargs["ttl"], 600)

    async def test_etag_from_the_response_is_stored(self):
        self.fetcher._client.get.return_value = make_response(
            json_body=make_jwks("kid-1"), headers={"ETag": '"abc123"'}
        )

        await self.fetcher.get_jwks(URL, expected_kid="kid-1")

        self.assertEqual(self.fetcher._mem[URL].etag, '"abc123"')

    async def test_second_fetch_sends_the_stored_etag(self):
        stale_entry = make_entry(kids=("kid-1",), expires_in=-10, etag='"abc123"')
        self.fetcher._mem[URL] = stale_entry

        await self.fetcher.get_jwks(URL, expected_kid="kid-1")

        sent_headers = self.fetcher._client.get.await_args.kwargs["headers"]
        self.assertEqual(sent_headers.get("If-None-Match"), '"abc123"')

    async def test_first_fetch_sends_no_if_none_match(self):
        await self.fetcher.get_jwks(URL, expected_kid="kid-1")

        sent_headers = self.fetcher._client.get.await_args.kwargs["headers"]
        self.assertNotIn("If-None-Match", sent_headers)


class Test304NotModified(JWKSFetcherTestBase):
    async def test_extends_the_existing_entry_and_returns_it(self):
        entry = make_entry(kids=("kid-1",), expires_in=-10, etag='"abc123"')
        self.fetcher._mem[URL] = entry
        self.fetcher._client.get.return_value = make_response(
            status_code=304, content=b""
        )

        result = await self.fetcher.get_jwks(URL, expected_kid="kid-1")

        self.assertIs(result, entry.jwks)
        self.assertGreater(entry.expires_at, time.time())

    async def test_does_not_write_back_to_the_distributed_cache(self):
        self.fetcher._mem[URL] = make_entry(
            kids=("kid-1",), expires_in=-10, etag='"abc123"'
        )
        self.fetcher._client.get.return_value = make_response(
            status_code=304, content=b""
        )

        await self.fetcher.get_jwks(URL, expected_kid="kid-1")

        self.jwks_cache.set_jwks.assert_not_awaited()


class TestFetchFailureStaleServing(JWKSFetcherTestBase):
    async def test_network_error_with_matching_stale_entry_serves_it(self):
        stale = make_entry(kids=("kid-1",), expires_in=-10)
        self.fetcher._mem[URL] = stale
        self.fetcher._client.get.side_effect = httpx.ConnectError("dns failure")

        result = await self.fetcher.get_jwks(URL, expected_kid="kid-1")

        self.assertIs(result, stale.jwks)

    async def test_http_error_status_with_matching_stale_entry_serves_it(self):
        stale = make_entry(kids=("kid-1",), expires_in=-10)
        self.fetcher._mem[URL] = stale
        self.fetcher._client.get.return_value = make_response(
            status_code=500, content=b"internal error"
        )

        result = await self.fetcher.get_jwks(URL, expected_kid="kid-1")

        self.assertIs(result, stale.jwks)

    async def test_network_error_with_no_entry_raises_503(self):
        self.fetcher._client.get.side_effect = httpx.ConnectError("dns failure")

        with self.assertRaises(HTTPException) as ctx:
            await self.fetcher.get_jwks(URL, expected_kid="kid-1")

        self.assertEqual(ctx.exception.status_code, 503)

    async def test_network_error_with_stale_entry_missing_the_kid_raises_503(self):
        self.fetcher._mem[URL] = make_entry(kids=("old-kid",), expires_in=-10)
        self.fetcher._client.get.side_effect = httpx.ConnectError("dns failure")

        with self.assertRaises(HTTPException) as ctx:
            await self.fetcher.get_jwks(URL, expected_kid="new-kid")

        self.assertEqual(ctx.exception.status_code, 503)

    async def test_malformed_response_body_is_treated_as_a_fetch_failure(self):
        self.fetcher._client.get.return_value = make_response(content=b"not json")

        with self.assertRaises(HTTPException) as ctx:
            await self.fetcher.get_jwks(URL, expected_kid="kid-1")

        self.assertEqual(ctx.exception.status_code, 503)

    async def test_response_with_no_keys_is_treated_as_a_fetch_failure(self):
        self.fetcher._client.get.return_value = make_response(json_body={"keys": []})

        with self.assertRaises(HTTPException) as ctx:
            await self.fetcher.get_jwks(URL, expected_kid="kid-1")

        self.assertEqual(ctx.exception.status_code, 503)


class TestConcurrency(JWKSFetcherTestBase):
    async def test_concurrent_requests_for_the_same_url_fetch_once(self):
        call_count = 0

        async def slow_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.02)
            return make_response(json_body=make_jwks("kid-1"))

        self.fetcher._client.get.side_effect = slow_get

        results = await asyncio.gather(
            *(self.fetcher.get_jwks(URL, expected_kid="kid-1") for _ in range(10))
        )

        self.assertEqual(call_count, 1)
        self.assertTrue(all(r == make_jwks("kid-1") for r in results))

    async def test_different_urls_do_not_share_a_lock(self):
        other_url = URL + "-other"
        self.fetcher._client.get.side_effect = [
            make_response(json_body=make_jwks("kid-1")),
            make_response(json_body=make_jwks("kid-2")),
        ]

        results = await asyncio.gather(
            self.fetcher.get_jwks(URL, expected_kid="kid-1"),
            self.fetcher.get_jwks(other_url, expected_kid="kid-2"),
        )

        self.assertEqual(self.fetcher._client.get.await_count, 2)
        self.assertEqual(results[0], make_jwks("kid-1"))
        self.assertEqual(results[1], make_jwks("kid-2"))


class TestAclose(JWKSFetcherTestBase):
    async def test_closes_the_http_client(self):
        await self.fetcher.aclose()

        self.fetcher._client.aclose.assert_awaited_once()


class TestPureHelpers(unittest.TestCase):
    def test_coerce_jwks_parses_a_json_string(self):
        import json

        result = _coerce_jwks(json.dumps(make_jwks("kid-1")))

        self.assertEqual(result, make_jwks("kid-1"))

    def test_coerce_jwks_rejects_a_non_dict(self):
        with self.assertRaises(ValueError):
            _coerce_jwks(["not", "a", "dict"])

    def test_coerce_jwks_rejects_missing_keys_field(self):
        with self.assertRaises(ValueError):
            _coerce_jwks({"no_keys_here": True})

    def test_coerce_jwks_rejects_empty_keys_list(self):
        with self.assertRaises(ValueError):
            _coerce_jwks({"keys": []})

    def test_parse_ttl_reads_max_age(self):
        resp = make_response(headers={"Cache-Control": "public, max-age=900"})

        self.assertEqual(_parse_ttl(resp, default_ttl=600), 900)

    def test_parse_ttl_falls_back_to_default_without_a_header(self):
        resp = make_response(headers={})

        self.assertEqual(_parse_ttl(resp, default_ttl=600), 600)

    def test_parse_ttl_clamps_to_the_minimum(self):
        resp = make_response(headers={"Cache-Control": "max-age=1"})

        self.assertEqual(_parse_ttl(resp, default_ttl=600), 60)

    def test_with_jitter_stays_within_ten_percent(self):
        for _ in range(200):
            jittered = _with_jitter(1000)
            self.assertGreaterEqual(jittered, 900)
            self.assertLessEqual(jittered, 1100)

    def test_with_jitter_never_drops_below_the_minimum(self):
        for _ in range(200):
            self.assertGreaterEqual(_with_jitter(60), 60)
