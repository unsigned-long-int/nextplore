import hashlib
import unittest

from nextplore_sdk.cache.utils.key_factory import get_cache_key, get_string_cache_key
from pydantic import BaseModel


class DummyModel(BaseModel):
    text: str


class TestKeyFactory(unittest.TestCase):
    def test_gets_string_key_with_prefix_and_salt(self):
        dummy_instance = DummyModel(text="test")
        prefix = "test-prefix"
        salt = "test"
        key = get_cache_key(dummy_instance, prefix=prefix, salt=salt)
        hashed = hashlib.sha256(
            f"{salt}:{dummy_instance.model_dump_json()}".encode()
        ).hexdigest()
        self.assertIn(f"{prefix}:", key)
        self.assertIn(hashed, key)

    def test_gets_string_cache_key_with_prefix_and_salt(self):
        string_key = "test-string-key"
        prefix = "test-prefix"
        salt = "test-salt"
        key = get_string_cache_key(value=string_key, prefix=prefix, salt=salt)
        hashed = hashlib.sha256(f"{salt}:{string_key}".encode()).hexdigest()
        self.assertIn(f"{prefix}:", key)
        self.assertIn(hashed, key)
