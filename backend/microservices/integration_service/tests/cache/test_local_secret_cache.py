import unittest
from unittest.mock import patch

from integration_service.cache.local_secret_cache import LocalTTLCache


class TestLocalTTLCache(unittest.TestCase):
    def setUp(self):
        self.now = 1_000.0
        patcher = patch("time.monotonic", side_effect=lambda: self.now)
        patcher.start()
        self.addCleanup(patcher.stop)

    def advance(self, secs: float) -> None:
        self.now += secs


class TestGetAndSet(TestLocalTTLCache):
    def test_get_missing_key_returns_none(self):
        cache = LocalTTLCache[str]()

        self.assertIsNone(cache.get("missing"))

    def test_set_then_get_returns_the_value(self):
        cache = LocalTTLCache[str]()

        cache.set("k", "v")

        self.assertEqual(cache.get("k"), "v")

    def test_set_overwrites_an_existing_value(self):
        cache = LocalTTLCache[str]()
        cache.set("k", "old")

        cache.set("k", "new")

        self.assertEqual(cache.get("k"), "new")

    def test_stores_falsy_values(self):
        cache = LocalTTLCache[int]()

        cache.set("zero", 0)

        self.assertEqual(cache.get("zero"), 0)

    def test_stores_none_values_indistinguishably_from_misses(self):
        cache = LocalTTLCache[None]()

        cache.set("k", None)

        self.assertIsNone(cache.get("k"))


class TestExpiry(TestLocalTTLCache):
    def test_returns_value_just_before_ttl(self):
        cache = LocalTTLCache[str](ttl_secs=10)
        cache.set("k", "v")

        self.advance(9.999)

        self.assertEqual(cache.get("k"), "v")

    def test_expires_exactly_at_ttl(self):
        cache = LocalTTLCache[str](ttl_secs=10)
        cache.set("k", "v")

        self.advance(10)

        self.assertIsNone(cache.get("k"))

    def test_expired_entry_is_removed_on_read(self):
        cache = LocalTTLCache[str](ttl_secs=10)
        cache.set("k", "v")
        self.advance(10)

        cache.get("k")

        self.assertNotIn("k", cache._store)

    def test_resetting_a_key_refreshes_its_ttl(self):
        cache = LocalTTLCache[str](ttl_secs=10)
        cache.set("k", "v")
        self.advance(8)

        cache.set("k", "v2")
        self.advance(8)

        self.assertEqual(cache.get("k"), "v2")

    def test_get_does_not_refresh_the_ttl(self):
        cache = LocalTTLCache[str](ttl_secs=10)
        cache.set("k", "v")
        self.advance(8)

        cache.get("k")
        self.advance(2)

        self.assertIsNone(cache.get("k"))

    def test_default_ttl_is_ten_minutes(self):
        cache = LocalTTLCache[str]()
        cache.set("k", "v")

        self.advance(599)
        self.assertEqual(cache.get("k"), "v")
        self.advance(1)
        self.assertIsNone(cache.get("k"))

    def test_expired_entries_are_not_purged_until_read(self):
        cache = LocalTTLCache[str](ttl_secs=10, maxsize=2)
        cache.set("a", "1")
        cache.set("b", "2")
        self.advance(10)

        cache.set("c", "3")

        self.assertNotIn("a", cache._store)
        self.assertIn("b", cache._store)


class TestEviction(TestLocalTTLCache):
    def test_does_not_evict_below_maxsize(self):
        cache = LocalTTLCache[str](maxsize=3)

        for key in ("a", "b", "c"):
            cache.set(key, key)

        self.assertEqual(sorted(cache._store), ["a", "b", "c"])

    def test_evicts_oldest_inserted_when_full(self):
        cache = LocalTTLCache[str](maxsize=2)
        cache.set("a", "1")
        cache.set("b", "2")

        cache.set("c", "3")

        self.assertIsNone(cache.get("a"))
        self.assertEqual(cache.get("b"), "2")
        self.assertEqual(cache.get("c"), "3")

    def test_never_exceeds_maxsize(self):
        cache = LocalTTLCache[int](maxsize=5)

        for i in range(50):
            cache.set(str(i), i)

        self.assertEqual(len(cache._store), 5)

    def test_maxsize_of_one_keeps_only_the_latest(self):
        cache = LocalTTLCache[str](maxsize=1)
        cache.set("a", "1")

        cache.set("b", "2")

        self.assertIsNone(cache.get("a"))
        self.assertEqual(cache.get("b"), "2")

    def test_eviction_is_fifo_not_lru(self):
        cache = LocalTTLCache[str](maxsize=2)
        cache.set("a", "1")
        cache.set("b", "2")
        cache.get("a")

        cache.set("c", "3")

        self.assertIsNone(cache.get("a"))

    def test_resetting_a_key_keeps_its_insertion_position(self):
        cache = LocalTTLCache[str](maxsize=2)
        cache.set("a", "1")
        cache.set("b", "2")
        cache.set("a", "1b")

        cache.set("c", "3")

        self.assertIsNone(cache.get("a"))
        self.assertEqual(cache.get("b"), "2")

    def test_resetting_an_existing_key_when_full_does_not_evict_another(self):
        cache = LocalTTLCache[str](maxsize=2)
        cache.set("a", "1")
        cache.set("b", "2")

        cache.set("b", "2b")

        self.assertEqual(cache.get("a"), "1")
        self.assertEqual(cache.get("b"), "2b")
        self.assertEqual(len(cache._store), 2)


class TestDeletePrefix(TestLocalTTLCache):
    def setUp(self):
        super().setUp()
        self.cache = LocalTTLCache[str]()
        for key in ("org:1:a", "org:1:b", "org:2:a", "user:1"):
            self.cache.set(key, key)

    def test_removes_all_keys_with_the_prefix(self):
        self.cache.delete_prefix("org:1:")

        self.assertIsNone(self.cache.get("org:1:a"))
        self.assertIsNone(self.cache.get("org:1:b"))

    def test_keeps_keys_without_the_prefix(self):
        self.cache.delete_prefix("org:1:")

        self.assertEqual(self.cache.get("org:2:a"), "org:2:a")
        self.assertEqual(self.cache.get("user:1"), "user:1")

    def test_prefix_match_is_exact_not_substring(self):
        self.cache.delete_prefix("1")

        self.assertEqual(len(self.cache._store), 4)

    def test_no_match_is_a_noop(self):
        self.cache.delete_prefix("nothing:")

        self.assertEqual(len(self.cache._store), 4)

    def test_empty_prefix_clears_everything(self):
        self.cache.delete_prefix("")

        self.assertEqual(len(self.cache._store), 0)

    def test_deleting_from_an_empty_cache_is_a_noop(self):
        cache = LocalTTLCache[str]()

        cache.delete_prefix("org:")

        self.assertEqual(len(cache._store), 0)