import logging
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

from vector_service.api.context import UserIdentity
from vector_service.domain.models import SemanticCacheMeta, SemanticMatch
from vector_service.services.vector_store_service.exceptions import (
    DeleteVectorDBFailed,
    SearchVectorDBFailed,
    UpsertVectorDBFailed,
)
from vector_service.services.vector_store_service.models import Vector, VectorPoint
from vector_service.services.vector_store_service.store.store_service import (
    VectorStoreService,
)

SERVICE_MODULE = "vector_service.services.vector_store_service.store.store_service"


def make_hit(score: float = 0.99, payload: dict | None = None):
    hit = MagicMock()
    hit.score = score
    hit.payload = payload if payload is not None else {}
    return hit


def make_response(points: list):
    response = MagicMock()
    response.points = points
    return response


def aware_iso(offset: timedelta) -> str:
    return (datetime.now(timezone.utc) + offset).isoformat()


def naive_iso(offset: timedelta) -> str:
    """An ISO timestamp with no UTC offset, as a sloppy writer would store it."""
    return (datetime.now(timezone.utc) + offset).replace(tzinfo=None).isoformat()


class VectorStoreServiceTestBase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client_mock = AsyncMock()
        self.client_mock.__class__.__name__ = "FakeStoreClient"

        self.service = VectorStoreService(client=self.client_mock)

        self.organization_id = uuid4()
        self.user_id = uuid4()
        self.identity = UserIdentity(
            organization_id=self.organization_id, user_id=self.user_id
        )

    def given_cache_hit(self, payload: dict, score: float = 0.99) -> None:
        self.client_mock.search_nearest_vectors.return_value = make_response(
            [make_hit(score=score, payload=payload)]
        )

    async def lookup(self) -> SemanticMatch | None:
        return await self.service.lookup_semantic_cache(
            user_identity=self.identity, embedding=[0.1, 0.2]
        )


class TestDeleteVectors(VectorStoreServiceTestBase):
    async def test_delegates_to_client(self):
        vector_ids = [str(uuid4()), str(uuid4())]

        await self.service.delete_vectors(
            vector_ids=vector_ids,
            user_id=str(self.user_id),
            organization_id=str(self.organization_id),
        )

        self.client_mock.delete_vectors.assert_awaited_once_with(
            vector_ids=vector_ids,
            user_id=str(self.user_id),
            organization_id=str(self.organization_id),
            collection="nextplore",
        )

    async def test_forwards_custom_collection(self):
        await self.service.delete_vectors(
            vector_ids=["a"],
            user_id=str(self.user_id),
            organization_id=str(self.organization_id),
            collection="archive",
        )

        kwargs = self.client_mock.delete_vectors.await_args.kwargs
        self.assertEqual(kwargs["collection"], "archive")

    async def test_empty_ids_short_circuits(self):
        await self.service.delete_vectors(
            vector_ids=[],
            user_id=str(self.user_id),
            organization_id=str(self.organization_id),
        )

        self.client_mock.delete_vectors.assert_not_awaited()

    async def test_domain_exception_passes_through_unchanged(self):
        original = DeleteVectorDBFailed("driver said no")
        self.client_mock.delete_vectors.side_effect = original

        with self.assertRaises(DeleteVectorDBFailed) as ctx:
            await self.service.delete_vectors(
                vector_ids=["a"],
                user_id=str(self.user_id),
                organization_id=str(self.organization_id),
            )

        self.assertIs(ctx.exception, original)

    async def test_unexpected_exception_is_wrapped_with_client_name(self):
        self.client_mock.delete_vectors.side_effect = RuntimeError("kaboom")

        with self.assertRaises(DeleteVectorDBFailed) as ctx:
            await self.service.delete_vectors(
                vector_ids=["a"],
                user_id=str(self.user_id),
                organization_id=str(self.organization_id),
            )

        self.assertIn("FakeStoreClient", str(ctx.exception))

    async def test_wrapped_exception_preserves_its_cause(self):
        original = RuntimeError("kaboom")
        self.client_mock.delete_vectors.side_effect = original

        with self.assertRaises(DeleteVectorDBFailed) as ctx:
            await self.service.delete_vectors(
                vector_ids=["a"],
                user_id=str(self.user_id),
                organization_id=str(self.organization_id),
            )

        self.assertIs(ctx.exception.__cause__, original)


class TestLookupSemanticCacheHits(VectorStoreServiceTestBase):
    async def test_returns_match_for_unexpired_entry(self):
        self.given_cache_hit(
            {
                "expires_at": aware_iso(timedelta(hours=1)),
                "json_payload": {"answer": "42"},
            }
        )

        result = await self.lookup()

        self.assertIsInstance(result, SemanticMatch)
        self.assertEqual(result.json_payload, {"answer": "42"})

    async def test_uses_only_the_first_hit(self):
        self.client_mock.search_nearest_vectors.return_value = make_response(
            [
                make_hit(
                    score=0.99,
                    payload={
                        "expires_at": aware_iso(timedelta(hours=1)),
                        "json_payload": {"answer": "first"},
                    },
                ),
                make_hit(
                    score=0.95,
                    payload={
                        "expires_at": aware_iso(timedelta(hours=1)),
                        "json_payload": {"answer": "second"},
                    },
                ),
            ]
        )

        result = await self.lookup()

        self.assertEqual(result.json_payload, {"answer": "first"})

    async def test_empty_json_payload_dict_is_returned_not_dropped(self):
        """`is None` rather than truthiness: an empty dict is a real value."""
        self.given_cache_hit(
            {"expires_at": aware_iso(timedelta(hours=1)), "json_payload": {}}
        )

        result = await self.lookup()

        self.assertIsInstance(result, SemanticMatch)
        self.assertEqual(result.json_payload, {})


class TestLookupSemanticCacheMisses(VectorStoreServiceTestBase):
    """Every malformed or stale entry must miss, never raise.

    A cache is an optimisation. If a corrupt entry can turn a lookup into an
    error, the cache becomes a liability rather than a speedup — one bad row
    would fail every query that matches it.
    """

    async def test_no_points(self):
        self.client_mock.search_nearest_vectors.return_value = make_response([])

        self.assertIsNone(await self.lookup())

    async def test_expired_entry(self):
        self.given_cache_hit(
            {
                "expires_at": aware_iso(timedelta(hours=-1)),
                "json_payload": {"answer": "stale"},
            }
        )

        self.assertIsNone(await self.lookup())

    async def test_missing_expires_at(self):
        self.given_cache_hit({"json_payload": {"answer": "42"}})

        self.assertIsNone(await self.lookup())

    async def test_empty_expires_at(self):
        self.given_cache_hit({"expires_at": "", "json_payload": {"answer": "42"}})

        self.assertIsNone(await self.lookup())

    async def test_unparseable_expires_at(self):
        self.given_cache_hit(
            {"expires_at": "not-a-date", "json_payload": {"answer": "42"}}
        )

        self.assertIsNone(await self.lookup())

    async def test_non_string_expires_at(self):
        self.given_cache_hit(
            {"expires_at": 1735689600, "json_payload": {"answer": "42"}}
        )

        self.assertIsNone(await self.lookup())

    async def test_missing_json_payload(self):
        self.given_cache_hit({"expires_at": aware_iso(timedelta(hours=1))})

        self.assertIsNone(await self.lookup())

    async def test_null_json_payload(self):
        self.given_cache_hit(
            {"expires_at": aware_iso(timedelta(hours=1)), "json_payload": None}
        )

        self.assertIsNone(await self.lookup())


class TestLookupSemanticCacheTimezones(VectorStoreServiceTestBase):
    async def test_naive_future_timestamp_is_read_as_utc_and_hits(self):
        """A naive timestamp is assumed UTC rather than raising.

        Comparing a naive datetime to an aware `now` raises TypeError, so
        without the normalisation this entry would fail the whole lookup.
        """
        self.given_cache_hit(
            {
                "expires_at": naive_iso(timedelta(hours=1)),
                "json_payload": {"answer": "42"},
            }
        )

        result = await self.lookup()

        self.assertIsInstance(result, SemanticMatch)

    async def test_naive_past_timestamp_is_read_as_utc_and_misses(self):
        self.given_cache_hit(
            {
                "expires_at": naive_iso(timedelta(hours=-1)),
                "json_payload": {"answer": "stale"},
            }
        )

        self.assertIsNone(await self.lookup())

    async def test_non_utc_offset_is_compared_correctly(self):
        """An entry written in a +02:00 offset must not be misread as UTC."""
        berlin = timezone(timedelta(hours=2))
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).astimezone(
            berlin
        )
        self.given_cache_hit(
            {
                "expires_at": expires_at.isoformat(),
                "json_payload": {"answer": "42"},
            }
        )

        result = await self.lookup()

        self.assertIsInstance(result, SemanticMatch)


class TestLookupSemanticCacheDelegation(VectorStoreServiceTestBase):
    async def test_cache_defaults(self):
        self.client_mock.search_nearest_vectors.return_value = make_response([])

        await self.lookup()

        kwargs = self.client_mock.search_nearest_vectors.await_args.kwargs
        self.assertEqual(kwargs["collection"], "nextplore-cache")
        self.assertEqual(kwargs["top_k"], 1)
        self.assertEqual(kwargs["score_threshold"], 0.92)
        self.assertIsNone(kwargs["refine_filters"])

    async def test_forwards_refine_filters_and_overrides(self):
        refine = [MagicMock()]
        self.client_mock.search_nearest_vectors.return_value = make_response([])

        await self.service.lookup_semantic_cache(
            user_identity=self.identity,
            embedding=[0.1],
            refine_filters=refine,
            score_threshold=0.75,
            top_k=3,
            collection="other-cache",
        )

        kwargs = self.client_mock.search_nearest_vectors.await_args.kwargs
        self.assertIs(kwargs["refine_filters"], refine)
        self.assertEqual(kwargs["score_threshold"], 0.75)
        self.assertEqual(kwargs["top_k"], 3)
        self.assertEqual(kwargs["collection"], "other-cache")

    async def test_passes_identity_straight_through(self):
        self.client_mock.search_nearest_vectors.return_value = make_response([])

        await self.lookup()

        kwargs = self.client_mock.search_nearest_vectors.await_args.kwargs
        self.assertIs(kwargs["user_identity"], self.identity)


class TestLookupSemanticCacheErrors(VectorStoreServiceTestBase):
    async def test_domain_exception_passes_through_unchanged(self):
        original = SearchVectorDBFailed("driver said no")
        self.client_mock.search_nearest_vectors.side_effect = original

        with self.assertRaises(SearchVectorDBFailed) as ctx:
            await self.lookup()

        self.assertIs(ctx.exception, original)

    async def test_unexpected_exception_is_wrapped_with_cause(self):
        original = RuntimeError("kaboom")
        self.client_mock.search_nearest_vectors.side_effect = original

        with self.assertRaises(SearchVectorDBFailed) as ctx:
            await self.lookup()

        self.assertIn("FakeStoreClient", str(ctx.exception))
        self.assertIs(ctx.exception.__cause__, original)

    async def test_cached_payload_is_not_logged_above_debug(self):
        """Cached answers are customer content; they must not reach INFO."""
        self.given_cache_hit(
            {
                "expires_at": aware_iso(timedelta(hours=1)),
                "json_payload": {"answer": "sensitive-customer-content"},
            }
        )

        with self.assertLogs(SERVICE_MODULE, level=logging.DEBUG) as logs:
            await self.lookup()

        above_debug = [
            record.getMessage()
            for record in logs.records
            if record.levelno > logging.DEBUG
        ]
        self.assertFalse(
            any("sensitive-customer-content" in line for line in above_debug)
        )


class TestStoreSemanticCacheEntry(VectorStoreServiceTestBase):
    def make_meta(self, **overrides) -> SemanticCacheMeta:
        payload = {
            "embedding": [0.1, 0.2, 0.3],
            "extra": {"provider": "openai", "model_id": "gpt-4o"},
        }
        payload.update(overrides)
        return SemanticCacheMeta(**payload)

    async def test_builds_point_from_identity_and_meta(self):
        meta = self.make_meta()

        await self.service.store_semantic_cache_entry(
            user_identity=self.identity, semantic_cache_meta=meta
        )

        points = self.client_mock.upsert_vectors.await_args.kwargs["vector_points"]

        self.assertEqual(len(points), 1)
        point = points[0]
        self.assertIsInstance(point, VectorPoint)
        self.assertEqual(point.user_id, self.user_id)
        self.assertEqual(point.organization_id, self.organization_id)
        self.assertEqual(point.vector, [0.1, 0.2, 0.3])
        self.assertEqual(point.extra, meta.extra)

    async def test_generates_a_fresh_id_per_entry(self):
        meta = self.make_meta()

        await self.service.store_semantic_cache_entry(
            user_identity=self.identity, semantic_cache_meta=meta
        )
        await self.service.store_semantic_cache_entry(
            user_identity=self.identity, semantic_cache_meta=meta
        )

        ids = [
            call.kwargs["vector_points"][0].id
            for call in self.client_mock.upsert_vectors.await_args_list
        ]
        self.assertEqual(len(set(ids)), 2)
        self.assertIsInstance(ids[0], UUID)

    async def test_uses_cache_collection_by_default(self):
        await self.service.store_semantic_cache_entry(
            user_identity=self.identity, semantic_cache_meta=self.make_meta()
        )

        kwargs = self.client_mock.upsert_vectors.await_args.kwargs
        self.assertEqual(kwargs["collection"], "nextplore-cache")

    async def test_forwards_custom_collection(self):
        await self.service.store_semantic_cache_entry(
            user_identity=self.identity,
            semantic_cache_meta=self.make_meta(),
            collection="other-cache",
        )

        kwargs = self.client_mock.upsert_vectors.await_args.kwargs
        self.assertEqual(kwargs["collection"], "other-cache")

    async def test_domain_exception_passes_through_unchanged(self):
        original = UpsertVectorDBFailed("driver said no")
        self.client_mock.upsert_vectors.side_effect = original

        with self.assertRaises(UpsertVectorDBFailed) as ctx:
            await self.service.store_semantic_cache_entry(
                user_identity=self.identity, semantic_cache_meta=self.make_meta()
            )

        self.assertIs(ctx.exception, original)

    async def test_unexpected_exception_is_wrapped_with_cause(self):
        original = RuntimeError("kaboom")
        self.client_mock.upsert_vectors.side_effect = original

        with self.assertRaises(UpsertVectorDBFailed) as ctx:
            await self.service.store_semantic_cache_entry(
                user_identity=self.identity, semantic_cache_meta=self.make_meta()
            )

        self.assertIn("FakeStoreClient", str(ctx.exception))
        self.assertIs(ctx.exception.__cause__, original)


class TestSearchNearestVectors(VectorStoreServiceTestBase):
    async def test_maps_hits_to_vectors(self):
        first_id, second_id = uuid4(), uuid4()
        self.client_mock.search_nearest_vectors.return_value = make_response(
            [
                make_hit(score=0.91, payload={"qdrant_vector_id": str(first_id)}),
                make_hit(score=0.84, payload={"qdrant_vector_id": str(second_id)}),
            ]
        )

        result = await self.service.search_nearest_vectors(
            user_identity=self.identity, embedding=[0.1]
        )

        self.assertEqual(
            result,
            [Vector(id=first_id, score=0.91), Vector(id=second_id, score=0.84)],
        )

    async def test_returns_empty_list_when_no_points(self):
        self.client_mock.search_nearest_vectors.return_value = make_response([])

        result = await self.service.search_nearest_vectors(
            user_identity=self.identity, embedding=[0.1]
        )

        self.assertEqual(result, [])

    async def test_skips_hits_without_a_vector_id(self):
        good_id = uuid4()
        self.client_mock.search_nearest_vectors.return_value = make_response(
            [
                make_hit(score=0.9, payload={}),
                make_hit(score=0.8, payload={"qdrant_vector_id": str(good_id)}),
            ]
        )

        result = await self.service.search_nearest_vectors(
            user_identity=self.identity, embedding=[0.1]
        )

        self.assertEqual(result, [Vector(id=good_id, score=0.8)])

    async def test_search_defaults(self):
        self.client_mock.search_nearest_vectors.return_value = make_response([])

        await self.service.search_nearest_vectors(
            user_identity=self.identity, embedding=[0.1]
        )

        kwargs = self.client_mock.search_nearest_vectors.await_args.kwargs
        self.assertEqual(kwargs["collection"], "nextplore")
        self.assertEqual(kwargs["top_k"], 5)

    async def test_does_not_pass_a_score_threshold(self):
        """Plain search is unfiltered by score; only the cache lookup sets one."""
        self.client_mock.search_nearest_vectors.return_value = make_response([])

        await self.service.search_nearest_vectors(
            user_identity=self.identity, embedding=[0.1]
        )

        kwargs = self.client_mock.search_nearest_vectors.await_args.kwargs
        self.assertNotIn("score_threshold", kwargs)

    async def test_forwards_overrides(self):
        self.client_mock.search_nearest_vectors.return_value = make_response([])

        await self.service.search_nearest_vectors(
            user_identity=self.identity,
            embedding=[0.1],
            top_k=20,
            collection="other",
        )

        kwargs = self.client_mock.search_nearest_vectors.await_args.kwargs
        self.assertEqual(kwargs["top_k"], 20)
        self.assertEqual(kwargs["collection"], "other")

    async def test_domain_exception_passes_through_unchanged(self):
        original = SearchVectorDBFailed("driver said no")
        self.client_mock.search_nearest_vectors.side_effect = original

        with self.assertRaises(SearchVectorDBFailed) as ctx:
            await self.service.search_nearest_vectors(
                user_identity=self.identity, embedding=[0.1]
            )

        self.assertIs(ctx.exception, original)

    async def test_unexpected_exception_is_wrapped(self):
        self.client_mock.search_nearest_vectors.side_effect = RuntimeError("kaboom")

        with self.assertRaises(SearchVectorDBFailed) as ctx:
            await self.service.search_nearest_vectors(
                user_identity=self.identity, embedding=[0.1]
            )

        self.assertIn("FakeStoreClient", str(ctx.exception))


class TestUpsertVectors(VectorStoreServiceTestBase):
    def make_point(self) -> VectorPoint:
        return VectorPoint(
            id=uuid4(),
            user_id=self.user_id,
            organization_id=self.organization_id,
            vector=[0.1, 0.2],
        )

    async def test_delegates_to_client(self):
        points = [self.make_point(), self.make_point()]

        await self.service.upsert_vectors(vector_points=points)

        self.client_mock.upsert_vectors.assert_awaited_once_with(
            vector_points=points, collection="nextplore"
        )

    async def test_empty_points_short_circuits(self):
        await self.service.upsert_vectors(vector_points=[])

        self.client_mock.upsert_vectors.assert_not_awaited()

    async def test_forwards_custom_collection(self):
        await self.service.upsert_vectors(
            vector_points=[self.make_point()], collection="archive"
        )

        kwargs = self.client_mock.upsert_vectors.await_args.kwargs
        self.assertEqual(kwargs["collection"], "archive")

    async def test_domain_exception_passes_through_unchanged(self):
        original = UpsertVectorDBFailed("driver said no")
        self.client_mock.upsert_vectors.side_effect = original

        with self.assertRaises(UpsertVectorDBFailed) as ctx:
            await self.service.upsert_vectors(vector_points=[self.make_point()])

        self.assertIs(ctx.exception, original)

    async def test_unexpected_exception_is_wrapped(self):
        self.client_mock.upsert_vectors.side_effect = RuntimeError("kaboom")

        with self.assertRaises(UpsertVectorDBFailed) as ctx:
            await self.service.upsert_vectors(vector_points=[self.make_point()])

        self.assertIn("FakeStoreClient", str(ctx.exception))


class TestAclose(VectorStoreServiceTestBase):
    async def test_closes_the_client(self):
        await self.service.aclose()

        self.client_mock.aclose.assert_awaited_once()

    async def test_close_failure_is_swallowed(self):
        self.client_mock.aclose.side_effect = RuntimeError("already closed")

        await self.service.aclose()

    async def test_close_failure_is_logged_at_debug(self):
        self.client_mock.aclose.side_effect = RuntimeError("already closed")

        with self.assertLogs(SERVICE_MODULE, level=logging.DEBUG) as logs:
            await self.service.aclose()

        self.assertTrue(any("close ignored" in line for line in logs.output))
