import json
import unittest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from nextplore_sdk.cache.client.base_redis_client import BaseCache
from pydantic import BaseModel
from pydantic.json import pydantic_encoder


class DummyModel(BaseModel):
    user_name: str
    user_id: str


class InvalidModel(BaseModel):
    whatever: str


class TestBaseCache(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.redis_client = AsyncMock()

    @patch("nextplore_sdk.cache.client.base_redis_client.get_redis_client")
    async def test_sets_and_build_base_cache(self, get_redis_client_mock):
        get_redis_client_mock.return_value = self.redis_client
        version = "test-version"
        namespace = "test-namespace"
        base_cache = BaseCache(namespace, version=version)
        self.assertEqual(self.redis_client, base_cache.redis)
        self.assertEqual(f"{namespace}:{version}:", base_cache.prefix)

    def test_build_key_from_mixed_parts(self):
        version = "test-version"
        namespace = "test-namespace"
        base_cache = BaseCache(
            namespace=namespace, version=version, redis=self.redis_client
        )
        uid_part = uuid.uuid4()
        parts = ["1", "2", "3", uid_part]
        key = base_cache._key(*parts)
        self.assertEqual(key, f"test-namespace:test-version:1:2:3:{uid_part!s}")

    async def test_returns_cached(self):
        version = "test-version"
        namespace = "test-namespace"
        dummy_model = DummyModel(user_name="test-user", user_id="test-user")
        self.redis_client.get.return_value = dummy_model.model_dump_json()
        base_cache = BaseCache(
            namespace=namespace, version=version, redis=self.redis_client
        )
        cached = await base_cache.get_one("whatever", model=DummyModel)
        self.assertEqual(cached.model_dump(), dummy_model.model_dump())
        self.redis_client.get.assert_awaited_once_with(base_cache._key("whatever"))

    async def test_returns_none_if_not_cached(self):
        version = "test-version"
        namespace = "test-namespace"
        self.redis_client.get.return_value = None
        base_cache = BaseCache(
            namespace=namespace, version=version, redis=self.redis_client
        )
        cached = await base_cache.get_one("whatever", model=DummyModel)
        self.assertIsNone(cached)
        self.redis_client.get.assert_awaited_once_with(base_cache._key("whatever"))

    async def test_deletes_invalid_model(self):
        version = "test-version"
        namespace = "test-namespace"
        self.redis_client.delete = AsyncMock()
        self.redis_client.get = AsyncMock()
        self.redis_client.get.return_value = InvalidModel(
            whatever="whatever"
        ).model_dump_json()
        base_cache = BaseCache(
            namespace=namespace, version=version, redis=self.redis_client
        )

        cached = await base_cache.get_one("whatever", model=DummyModel)
        self.redis_client.delete.assert_awaited_once_with(base_cache._key("whatever"))
        self.redis_client.get.assert_awaited_once_with(base_cache._key("whatever"))
        self.assertIsNone(cached)

    async def test_deletes_invalid_json(self):
        version = "test-version"
        namespace = "test-namespace"
        self.redis_client.delete = AsyncMock()
        self.redis_client.get = AsyncMock()
        self.redis_client.get.return_value = "i am invalid json"
        base_cache = BaseCache(
            namespace=namespace, version=version, redis=self.redis_client
        )

        cached = await base_cache.get_one("whatever", model=DummyModel)
        self.redis_client.delete.assert_awaited_once_with(base_cache._key("whatever"))
        self.redis_client.get.assert_awaited_once_with(base_cache._key("whatever"))
        self.assertIsNone(cached)

    async def test_sets_one_with_default_ttl(self):
        version = "test-version"
        namespace = "test-namespace"
        dummy_model = DummyModel(user_name="test-user", user_id="test-user")
        self.redis_client.set = AsyncMock()
        base_cache = BaseCache(
            namespace=namespace, version=version, redis=self.redis_client
        )
        await base_cache.set_one("whatever", value=dummy_model)
        self.redis_client.set.assert_awaited_once_with(
            base_cache._key("whatever"),
            value=dummy_model.model_dump_json(),
            ex=base_cache.default_ttl,
        )

    async def test_gets_many_models(self):
        version = "test-version"
        namespace = "test-namespace"
        dummy_models = [
            DummyModel(user_name="test-user1", user_id="test-user1"),
            DummyModel(user_name="test-user2", user_id="test-user2"),
        ]
        self.redis_client.get.return_value = json.dumps(
            dummy_models, default=pydantic_encoder
        )
        base_cache = BaseCache(
            namespace=namespace, version=version, redis=self.redis_client
        )
        cached = await base_cache.get_many("whatever", model=DummyModel)
        self.assertEqual(len(cached), len(dummy_models))
        self.assertEqual(cached[0].model_dump(), dummy_models[0].model_dump())
        self.redis_client.get.assert_awaited_once_with(base_cache._key("whatever"))

    async def test_deletes_by_invalid_model(self):
        version = "test-version"
        namespace = "test-namespace"
        dummy_models = [
            DummyModel(user_name="test-user1", user_id="test-user1"),
            DummyModel(user_name="test-user2", user_id="test-user2"),
        ]
        self.redis_client.delete = AsyncMock()
        self.redis_client.get.return_value = json.dumps(
            dummy_models, default=pydantic_encoder
        )
        base_cache = BaseCache(
            namespace=namespace, version=version, redis=self.redis_client
        )
        cached = await base_cache.get_many("whatever", model=InvalidModel)
        self.assertEqual(len(cached), 0)
        self.redis_client.delete.assert_awaited_once_with(base_cache._key("whatever"))

    async def test_deletes_by_invalid_json(self):
        version = "test-version"
        namespace = "test-namespace"
        self.redis_client.delete = AsyncMock()
        self.redis_client.get.return_value = "i am invalid json"
        base_cache = BaseCache(
            namespace=namespace, version=version, redis=self.redis_client
        )
        cached = await base_cache.get_many("whatever", model=InvalidModel)
        self.assertEqual(len(cached), 0)
        self.redis_client.delete.assert_awaited_once_with(base_cache._key("whatever"))

    async def test_sets_many_with_default_ttl(self):
        version = "test-version"
        namespace = "test-namespace"
        self.redis_client.set = AsyncMock()
        self.redis_client.get.return_value = "i am invalid json"
        base_cache = BaseCache(
            namespace=namespace, version=version, redis=self.redis_client
        )
        dummy_models = [
            DummyModel(user_name="test-user1", user_id="test-user1"),
            DummyModel(user_name="test-user2", user_id="test-user2"),
        ]
        await base_cache.set_many("whatever", value=dummy_models)
        self.redis_client.set.assert_awaited_once_with(
            base_cache._key("whatever"),
            value=json.dumps(dummy_models, default=pydantic_encoder),
            ex=base_cache.default_ttl,
        )

    async def test_gets_raw(self):
        version = "test-version"
        namespace = "test-namespace"
        self.redis_client.set = AsyncMock()
        raw_dict = {"type": "raw dict"}
        self.redis_client.get.return_value = json.dumps(raw_dict)
        base_cache = BaseCache(
            namespace=namespace, version=version, redis=self.redis_client
        )
        raw = await base_cache.get_raw("whatever")
        self.assertEqual(raw, raw_dict)

    async def test_deletes_by_decode_error(self):
        version = "test-version"
        namespace = "test-namespace"
        self.redis_client.delete = AsyncMock()
        self.redis_client.set = AsyncMock()
        invalid = "invalid json"
        self.redis_client.get.return_value = invalid
        base_cache = BaseCache(
            namespace=namespace, version=version, redis=self.redis_client
        )
        raw = await base_cache.get_raw("whatever")
        self.assertIsNone(raw)
        self.redis_client.delete.assert_awaited_once_with(base_cache._key("whatever"))

    async def test_sets_raw_with_custom_ttl(self):
        version = "test-version"
        namespace = "test-namespace"
        raw_value = {"type": "raw dict"}
        custom_ttl = 5
        self.redis_client.set = AsyncMock()
        base_cache = BaseCache(
            namespace=namespace, version=version, redis=self.redis_client
        )
        await base_cache.set_raw("whatever", value=raw_value, ttl=custom_ttl)
        self.redis_client.set.assert_awaited_once_with(
            base_cache._key("whatever"), value=json.dumps(raw_value), ex=custom_ttl
        )

    async def test_deletes_with_key(self):
        version = "test-version"
        namespace = "test-namespace"
        self.redis_client.delete = AsyncMock()
        base_cache = BaseCache(
            namespace=namespace, version=version, redis=self.redis_client
        )
        await base_cache.delete("whatever")
        self.redis_client.delete.assert_awaited_once_with(base_cache._key("whatever"))

    async def test_delete_by_prefix_deletes_only_matching(self):
        version = "test-version"
        namespace = "test-namespace"
        base_cache = BaseCache(
            namespace=namespace, version=version, redis=self.redis_client
        )

        all_keys = [
            "test-namespace:test-version:a:1",
            "test-namespace:test-version:a:2",
            "test-namespace:test-version:a:sub:3",
            "test-namespace:test-version:b:1",
            "otherns:test-version:a:1",
        ]

        def scan_iter_mock(*, match=None, count=None):
            prefix = match[:-1] if match and match.endswith("*") else match

            async def gen():
                for k in all_keys:
                    if prefix is None or (prefix and k.startswith(prefix)):
                        yield k

            return gen()

        self.redis_client.scan_iter = unittest.mock.MagicMock(
            side_effect=scan_iter_mock
        )

        class Pipe:
            def __init__(self):
                self.calls = []

            def delete(self, k):
                self.calls.append(k)

            async def execute(self):
                return None

        pipe = Pipe()
        self.redis_client.pipeline = unittest.mock.MagicMock(return_value=pipe)

        await base_cache.delete_by_prefix("a")

        expected = {
            "test-namespace:test-version:a:1",
            "test-namespace:test-version:a:2",
            "test-namespace:test-version:a:sub:3",
        }
        self.assertEqual(set(pipe.calls), expected)

        expected_pattern = base_cache._key("a") + "*"
        self.redis_client.scan_iter.assert_called_once_with(
            match=expected_pattern, count=100
        )

    async def test_delete_by_prefix_batches(self):
        version = "test-version"
        namespace = "test-namespace"
        base_cache = BaseCache(
            namespace=namespace, version=version, redis=self.redis_client
        )

        keys = [f"test-namespace:test-version:a:{i}" for i in range(205)]

        async def gen():
            for k in keys:
                yield k

        self.redis_client.scan_iter = MagicMock(return_value=gen())

        class Pipe:
            def __init__(self):
                self.exec_count = 0
                self.batch_sizes = []
                self._current = 0

            def delete(self, _k):
                self._current += 1

            async def execute(self):
                self.exec_count += 1
                self.batch_sizes.append(self._current)
                self._current = 0

        pipe = Pipe()
        self.redis_client.pipeline = MagicMock(return_value=pipe)

        await base_cache.delete_by_prefix("a", batch_size=100)

        self.assertEqual(pipe.exec_count, 3)
        self.assertEqual(pipe.batch_sizes, [100, 100, 5])

        expected_pattern = base_cache._key("a") + "*"
        self.redis_client.scan_iter.assert_called_once_with(
            match=expected_pattern, count=100
        )
