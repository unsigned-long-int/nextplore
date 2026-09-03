import unittest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse
from qdrant_client.http.models import (
    FieldCondition,
    FilterSelector,
    MatchAny,
    MatchValue,
)

from vector_service.api.context import UserIdentity
from vector_service.services.vector_store_service.clients.qdrant_store_client import (
    QDrantStoreClient,
)
from vector_service.services.vector_store_service.exceptions import (
    DeleteVectorDBFailed,
    SearchVectorDBFailed,
    UpsertVectorDBFailed,
)
from vector_service.services.vector_store_service.models import VectorPoint

CLIENT_PATH = (
    "vector_service.services.vector_store_service.clients."
    "qdrant_store_client.AsyncQdrantClient"
)


def unexpected_response(status_code: int = 500) -> UnexpectedResponse:
    return UnexpectedResponse(
        status_code=status_code,
        reason_phrase="Internal Server Error",
        content=b"boom",
        headers=None,
    )


class QDrantStoreClientTestBase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        patcher = patch(CLIENT_PATH)
        self.async_client_cls = patcher.start()
        self.addCleanup(patcher.stop)

        self.qdrant_mock = AsyncMock()
        self.async_client_cls.return_value = self.qdrant_mock

        self.client = QDrantStoreClient(
            cluster_host="https://qdrant.example", api_key="test-key"
        )

        self.organization_id = uuid4()
        self.user_id = uuid4()
        self.identity = UserIdentity(
            organization_id=self.organization_id, user_id=self.user_id
        )

    @staticmethod
    def conditions_as_pairs(conditions) -> list[tuple[str, object]]:
        pairs = []
        for condition in conditions:
            match = condition.match
            value = getattr(match, "value", None)
            if value is None:
                value = getattr(match, "any", None)
            pairs.append((condition.key, value))
        return pairs


class TestInit(QDrantStoreClientTestBase):
    def test_passes_host_and_api_key_to_the_driver(self):
        self.async_client_cls.assert_called_once_with(
            url="https://qdrant.example", api_key="test-key"
        )


class TestSearchNearestVectors(QDrantStoreClientTestBase):
    async def test_returns_driver_response(self):
        expected = object()
        self.qdrant_mock.query_points.return_value = expected

        result = await self.client.search_nearest_vectors(
            user_identity=self.identity, embedding=[0.1, 0.2]
        )

        self.assertIs(result, expected)
        self.qdrant_mock.query_points.assert_awaited_once()

    async def test_always_filters_on_user_and_organization(self):
        await self.client.search_nearest_vectors(
            user_identity=self.identity, embedding=[0.1]
        )

        kwargs = self.qdrant_mock.query_points.await_args.kwargs
        pairs = self.conditions_as_pairs(kwargs["query_filter"].must)

        self.assertIn(("user_id", str(self.user_id)), pairs)
        self.assertIn(("organization_id", str(self.organization_id)), pairs)

    async def test_tenant_conditions_come_before_refine_filters(self):
        refine = [
            FieldCondition(key="provider", match=MatchValue(value="openai")),
        ]

        await self.client.search_nearest_vectors(
            user_identity=self.identity, embedding=[0.1], refine_filters=refine
        )

        kwargs = self.qdrant_mock.query_points.await_args.kwargs
        pairs = self.conditions_as_pairs(kwargs["query_filter"].must)

        self.assertEqual(
            pairs,
            [
                ("user_id", str(self.user_id)),
                ("organization_id", str(self.organization_id)),
                ("provider", "openai"),
            ],
        )

    async def test_refine_filters_cannot_replace_tenant_conditions(self):
        attacker_id = uuid4()
        refine = [
            FieldCondition(key="user_id", match=MatchValue(value=str(attacker_id))),
        ]

        await self.client.search_nearest_vectors(
            user_identity=self.identity, embedding=[0.1], refine_filters=refine
        )

        kwargs = self.qdrant_mock.query_points.await_args.kwargs
        pairs = self.conditions_as_pairs(kwargs["query_filter"].must)

        self.assertEqual(
            pairs,
            [
                ("user_id", str(self.user_id)),
                ("organization_id", str(self.organization_id)),
                ("user_id", str(attacker_id)),
            ],
        )

    async def test_none_refine_filters_yields_only_tenant_conditions(self):
        await self.client.search_nearest_vectors(
            user_identity=self.identity, embedding=[0.1], refine_filters=None
        )

        kwargs = self.qdrant_mock.query_points.await_args.kwargs
        self.assertEqual(len(kwargs["query_filter"].must), 2)

    async def test_default_arguments(self):
        await self.client.search_nearest_vectors(
            user_identity=self.identity, embedding=[0.1]
        )

        kwargs = self.qdrant_mock.query_points.await_args.kwargs
        self.assertEqual(kwargs["collection_name"], "nextplore")
        self.assertEqual(kwargs["limit"], 5)
        self.assertTrue(kwargs["with_payload"])
        self.assertFalse(kwargs["with_vectors"])
        self.assertIsNone(kwargs["score_threshold"])

    async def test_overridden_arguments_are_forwarded(self):
        await self.client.search_nearest_vectors(
            user_identity=self.identity,
            embedding=[0.1, 0.2, 0.3],
            top_k=25,
            collection="other",
            score_threshold=0.82,
        )

        kwargs = self.qdrant_mock.query_points.await_args.kwargs
        self.assertEqual(kwargs["collection_name"], "other")
        self.assertEqual(kwargs["limit"], 25)
        self.assertEqual(kwargs["score_threshold"], 0.82)
        self.assertEqual(kwargs["query"], [0.1, 0.2, 0.3])

    async def test_response_handling_exception_is_wrapped(self):
        original = ResponseHandlingException("connection reset")
        self.qdrant_mock.query_points.side_effect = original

        with self.assertRaises(SearchVectorDBFailed) as ctx:
            await self.client.search_nearest_vectors(
                user_identity=self.identity, embedding=[0.1]
            )

        self.assertIn("response handling failed", str(ctx.exception))
        self.assertIs(ctx.exception.__cause__, original)

    async def test_unexpected_response_reports_status_code(self):
        self.qdrant_mock.query_points.side_effect = unexpected_response(503)

        with self.assertRaises(SearchVectorDBFailed) as ctx:
            await self.client.search_nearest_vectors(
                user_identity=self.identity, embedding=[0.1]
            )

        self.assertIn("503", str(ctx.exception))

    async def test_generic_exception_is_wrapped(self):
        self.qdrant_mock.query_points.side_effect = RuntimeError("kaboom")

        with self.assertRaises(SearchVectorDBFailed) as ctx:
            await self.client.search_nearest_vectors(
                user_identity=self.identity, embedding=[0.1]
            )

        self.assertIn("unexpected exception", str(ctx.exception))

    async def test_error_message_does_not_leak_the_embedding(self):
        self.qdrant_mock.query_points.side_effect = RuntimeError("kaboom")

        with self.assertRaises(SearchVectorDBFailed) as ctx:
            await self.client.search_nearest_vectors(
                user_identity=self.identity, embedding=[0.123456, 0.98765]
            )

        self.assertNotIn("0.123456", str(ctx.exception))


class TestDeleteVectors(QDrantStoreClientTestBase):
    async def test_builds_filter_selector_with_all_three_conditions(self):
        vector_ids = [str(uuid4()), str(uuid4())]

        await self.client.delete_vectors(
            vector_ids=vector_ids,
            user_id=str(self.user_id),
            organization_id=str(self.organization_id),
        )

        kwargs = self.qdrant_mock.delete.await_args.kwargs
        selector = kwargs["points_selector"]

        self.assertIsInstance(selector, FilterSelector)
        pairs = self.conditions_as_pairs(selector.filter.must)
        self.assertEqual(
            pairs,
            [
                ("qdrant_vector_id", vector_ids),
                ("organization_id", str(self.organization_id)),
                ("user_id", str(self.user_id)),
            ],
        )

    async def test_vector_ids_use_match_any(self):
        await self.client.delete_vectors(
            vector_ids=["a", "b", "c"],
            user_id=str(self.user_id),
            organization_id=str(self.organization_id),
        )

        selector = self.qdrant_mock.delete.await_args.kwargs["points_selector"]
        self.assertIsInstance(selector.filter.must[0].match, MatchAny)

    async def test_empty_vector_ids_does_not_call_delete(self):
        await self.client.delete_vectors(
            vector_ids=[],
            user_id=str(self.user_id),
            organization_id=str(self.organization_id),
        )
        self.qdrant_mock.delete.assert_not_awaited()

    async def test_empty_point_list_does_not_call_upsert(self):
        await self.client.upsert_vectors([])
        self.qdrant_mock.upsert.assert_not_awaited()

    async def test_deletion_is_scoped_to_the_tenant(self):
        await self.client.delete_vectors(
            vector_ids=["a"],
            user_id=str(self.user_id),
            organization_id=str(self.organization_id),
        )

        selector = self.qdrant_mock.delete.await_args.kwargs["points_selector"]
        keys = [c.key for c in selector.filter.must]
        self.assertIn("organization_id", keys)
        self.assertIn("user_id", keys)

    async def test_uses_default_collection(self):
        await self.client.delete_vectors(
            vector_ids=["a"],
            user_id=str(self.user_id),
            organization_id=str(self.organization_id),
        )

        kwargs = self.qdrant_mock.delete.await_args.kwargs
        self.assertEqual(kwargs["collection_name"], "nextplore")

    async def test_custom_collection_is_forwarded(self):
        await self.client.delete_vectors(
            vector_ids=["a"],
            user_id=str(self.user_id),
            organization_id=str(self.organization_id),
            collection="archive",
        )

        kwargs = self.qdrant_mock.delete.await_args.kwargs
        self.assertEqual(kwargs["collection_name"], "archive")

    async def test_failure_is_wrapped(self):
        original = RuntimeError("kaboom")
        self.qdrant_mock.delete.side_effect = original

        with self.assertRaises(DeleteVectorDBFailed) as ctx:
            await self.client.delete_vectors(
                vector_ids=["a"],
                user_id=str(self.user_id),
                organization_id=str(self.organization_id),
            )

        self.assertIs(ctx.exception.__cause__, original)

    async def test_unexpected_response_is_wrapped_as_delete_failure(self):
        self.qdrant_mock.delete.side_effect = unexpected_response(404)

        with self.assertRaises(DeleteVectorDBFailed):
            await self.client.delete_vectors(
                vector_ids=["a"],
                user_id=str(self.user_id),
                organization_id=str(self.organization_id),
            )


class TestUpsertVectors(QDrantStoreClientTestBase):
    def make_point(self, **overrides) -> VectorPoint:
        payload = {
            "id": uuid4(),
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "vector": [0.1, 0.2],
            "extra": {"table_name": "orders"},
        }
        payload.update(overrides)
        return VectorPoint(**payload)

    async def test_maps_point_fields_into_payload(self):
        point = self.make_point()

        await self.client.upsert_vectors([point])

        kwargs = self.qdrant_mock.upsert.await_args.kwargs
        struct = kwargs["points"][0]

        self.assertEqual(struct.id, str(point.id))
        self.assertEqual(struct.vector, [0.1, 0.2])
        self.assertEqual(struct.payload["qdrant_vector_id"], str(point.id))
        self.assertEqual(struct.payload["user_id"], str(self.user_id))
        self.assertEqual(struct.payload["organization_id"], str(self.organization_id))
        self.assertEqual(struct.payload["table_name"], "orders")

    async def test_maps_every_point(self):
        points = [self.make_point() for _ in range(3)]

        await self.client.upsert_vectors(points)

        structs = self.qdrant_mock.upsert.await_args.kwargs["points"]
        self.assertEqual(len(structs), 3)
        self.assertEqual({s.id for s in structs}, {str(p.id) for p in points})

    async def test_empty_extra_yields_only_tenant_keys(self):
        point = self.make_point(extra={})

        await self.client.upsert_vectors([point])

        struct = self.qdrant_mock.upsert.await_args.kwargs["points"][0]
        self.assertEqual(
            set(struct.payload),
            {"qdrant_vector_id", "user_id", "organization_id"},
        )

    async def test_custom_collection_is_forwarded(self):
        await self.client.upsert_vectors([self.make_point()], collection="archive")

        kwargs = self.qdrant_mock.upsert.await_args.kwargs
        self.assertEqual(kwargs["collection_name"], "archive")

    async def test_failure_is_wrapped(self):
        original = RuntimeError("kaboom")
        self.qdrant_mock.upsert.side_effect = original

        with self.assertRaises(UpsertVectorDBFailed) as ctx:
            await self.client.upsert_vectors([self.make_point()])

        self.assertIn("unexpected exception", str(ctx.exception))
        self.assertIs(ctx.exception.__cause__, original)


class TestAclose(QDrantStoreClientTestBase):
    async def test_closes_the_driver(self):
        await self.client.aclose()

        self.qdrant_mock.close.assert_awaited_once()

    async def test_close_failure_is_swallowed(self):
        self.qdrant_mock.close.side_effect = RuntimeError("already closed")

        await self.client.aclose()

    async def test_close_failure_is_logged_at_debug(self):
        self.qdrant_mock.close.side_effect = RuntimeError("already closed")

        with self.assertLogs(
            "vector_service.services.vector_store_service.clients.qdrant_store_client",
            level="DEBUG",
        ) as logs:
            await self.client.aclose()

        self.assertTrue(any("close ignored" in line for line in logs.output))
