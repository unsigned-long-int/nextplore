import json
import unittest
from uuid import UUID, uuid4

from nextplore_sdk.encryptor.client.aad_serializer import serialize_aad


class TestSerializeAAD(unittest.TestCase):
    def test_serializes_empty_dict(self):
        aad = {}

        result = serialize_aad(aad)

        self.assertEqual(result, b"{}")
        self.assertIsInstance(result, bytes)

    def test_serializes_string_values(self):
        aad = {"key1": "value1", "key2": "value2", "key3": "value3"}

        result = serialize_aad(aad)

        expected = b'{"key1":"value1","key2":"value2","key3":"value3"}'
        self.assertEqual(result, expected)
        self.assertIsInstance(result, bytes)

    def test_converts_uuid_to_string(self):
        test_uuid = uuid4()
        aad = {"user_id": test_uuid}

        result = serialize_aad(aad)

        self.assertIsInstance(result, bytes)
        decoded = json.loads(result.decode())
        self.assertEqual(decoded["user_id"], str(test_uuid))
        self.assertIsInstance(decoded["user_id"], str)

    def test_converts_multiple_uuids(self):
        org_id = uuid4()
        user_id = uuid4()
        integration_id = uuid4()

        aad = {
            "organization_id": org_id,
            "user_id": user_id,
            "integration_id": integration_id,
        }

        result = serialize_aad(aad)

        decoded = json.loads(result.decode())
        self.assertEqual(decoded["organization_id"], str(org_id))
        self.assertEqual(decoded["user_id"], str(user_id))
        self.assertEqual(decoded["integration_id"], str(integration_id))

    def test_mixes_strings_and_uuids(self):
        test_uuid = uuid4()
        aad = {
            "string_key": "string_value",
            "uuid_key": test_uuid,
            "another_string": "another_value",
        }

        result = serialize_aad(aad)

        decoded = json.loads(result.decode())
        self.assertEqual(decoded["string_key"], "string_value")
        self.assertEqual(decoded["uuid_key"], str(test_uuid))
        self.assertEqual(decoded["another_string"], "another_value")

    def test_returns_bytes_type(self):
        aad = {"key": "value"}

        result = serialize_aad(aad)

        self.assertIsInstance(result, bytes)
        self.assertNotIsInstance(result, str)

    def test_uses_compact_json_format(self):
        aad = {"key1": "value1", "key2": "value2"}

        result = serialize_aad(aad)

        self.assertNotIn(b": ", result)
        self.assertNotIn(b", ", result)
        self.assertIn(b":", result)
        self.assertIn(b",", result)

    def test_preserves_key_order(self):
        aad = {"first": "a", "second": "b", "third": "c"}

        result = serialize_aad(aad)

        decoded = result.decode()
        first_pos = decoded.index("first")
        second_pos = decoded.index("second")
        third_pos = decoded.index("third")
        self.assertLess(first_pos, second_pos)
        self.assertLess(second_pos, third_pos)

    def test_handles_special_characters_in_strings(self):
        aad = {
            "key": 'value with "quotes" and \\backslash',
            "another": "newline\nand\ttab",
        }

        result = serialize_aad(aad)

        decoded = json.loads(result.decode())
        self.assertEqual(decoded["key"], 'value with "quotes" and \\backslash')
        self.assertEqual(decoded["another"], "newline\nand\ttab")

    def test_output_is_valid_json(self):
        test_uuid = uuid4()
        aad = {"org_id": test_uuid, "name": "test"}

        result = serialize_aad(aad)

        decoded = json.loads(result.decode())
        self.assertIsInstance(decoded, dict)
        self.assertEqual(len(decoded), 2)

    def test_consistent_serialization_for_same_input(self):
        test_uuid = uuid4()
        aad = {"user_id": test_uuid, "action": "encrypt"}

        result1 = serialize_aad(aad)
        result2 = serialize_aad(aad)

        self.assertEqual(result1, result2)

    def test_different_uuids_produce_different_output(self):
        uuid1 = uuid4()
        uuid2 = uuid4()
        aad1 = {"id": uuid1}
        aad2 = {"id": uuid2}

        result1 = serialize_aad(aad1)
        result2 = serialize_aad(aad2)

        self.assertNotEqual(result1, result2)

    def test_handles_uuid_in_different_positions(self):
        uuid1 = uuid4()
        uuid2 = uuid4()

        aad = {
            "first_string": "value1",
            "first_uuid": uuid1,
            "middle_string": "value2",
            "second_uuid": uuid2,
            "last_string": "value3",
        }

        result = serialize_aad(aad)

        decoded = json.loads(result.decode())
        self.assertEqual(decoded["first_uuid"], str(uuid1))
        self.assertEqual(decoded["second_uuid"], str(uuid2))
        self.assertEqual(decoded["first_string"], "value1")
        self.assertEqual(decoded["middle_string"], "value2")
        self.assertEqual(decoded["last_string"], "value3")

    def test_uuid_string_format_is_lowercase_with_hyphens(self):
        test_uuid = UUID("550e8400-e29b-41d4-a716-446655440000")
        aad = {"id": test_uuid}

        result = serialize_aad(aad)

        decoded = json.loads(result.decode())
        self.assertEqual(decoded["id"], "550e8400-e29b-41d4-a716-446655440000")
        uuid_str = decoded["id"]
        parts = uuid_str.split("-")
        self.assertEqual(len(parts), 5)
        self.assertEqual(len(parts[0]), 8)
        self.assertEqual(len(parts[1]), 4)
        self.assertEqual(len(parts[2]), 4)
        self.assertEqual(len(parts[3]), 4)
        self.assertEqual(len(parts[4]), 12)

    def test_real_world_encryption_scenario(self):
        org_id = uuid4()
        user_id = uuid4()
        integration_id = uuid4()

        aad = {
            "organization_id": org_id,
            "user_id": user_id,
            "integration_id": integration_id,
        }

        result = serialize_aad(aad)

        self.assertIsInstance(result, bytes)
        decoded = json.loads(result.decode())

        self.assertIsInstance(decoded["organization_id"], str)
        self.assertIsInstance(decoded["user_id"], str)
        self.assertIsInstance(decoded["integration_id"], str)

        self.assertEqual(decoded["organization_id"], str(org_id))
        self.assertEqual(decoded["user_id"], str(user_id))
        self.assertEqual(decoded["integration_id"], str(integration_id))

        self.assertNotIn(b" ", result)

    def test_can_roundtrip_through_deserialization(self):
        original_uuid = uuid4()
        aad = {"user_id": original_uuid, "action": "test"}

        serialized = serialize_aad(aad)
        deserialized = json.loads(serialized.decode())

        self.assertEqual(deserialized["user_id"], str(original_uuid))
        self.assertEqual(deserialized["action"], "test")

        reconstructed_uuid = UUID(deserialized["user_id"])
        self.assertEqual(reconstructed_uuid, original_uuid)

    def test_handles_single_key_value_pair(self):
        test_uuid = uuid4()
        aad = {"id": test_uuid}

        result = serialize_aad(aad)

        expected = json.dumps({"id": str(test_uuid)}, separators=(",", ":")).encode()
        self.assertEqual(result, expected)


class TestSerializeAADEdgeCases(unittest.TestCase):
    def test_handles_empty_string_value(self):
        aad = {"key": ""}

        result = serialize_aad(aad)

        decoded = json.loads(result.decode())
        self.assertEqual(decoded["key"], "")

    def test_handles_unicode_characters(self):
        aad = {"name": "José García", "city": "東京", "emoji": "🔐"}

        result = serialize_aad(aad)

        decoded = json.loads(result.decode())
        self.assertEqual(decoded["name"], "José García")
        self.assertEqual(decoded["city"], "東京")
        self.assertEqual(decoded["emoji"], "🔐")

    def test_key_with_special_characters(self):
        test_uuid = uuid4()
        aad = {"user-id": test_uuid, "org_id": "test", "action.type": "encrypt"}

        result = serialize_aad(aad)

        decoded = json.loads(result.decode())
        self.assertEqual(decoded["user-id"], str(test_uuid))
        self.assertEqual(decoded["org_id"], "test")
        self.assertEqual(decoded["action.type"], "encrypt")
