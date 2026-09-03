import datetime
import unittest
from uuid import uuid4

from kafka_messaging.codec.utils import to_avro_values


class TestUtils(unittest.TestCase):
    def test_uuid_to_str(self):
        test_uuid = uuid4()
        res = to_avro_values(test_uuid)
        self.assertEqual(str(test_uuid), res)
        self.assertIsInstance(res, str)

    def test_dt_to_int(self):
        test_dt = datetime.datetime(2020, 1, 1)
        test_res = int(
            test_dt.replace(tzinfo=datetime.timezone.utc).timestamp() * 1_000_000
        )
        res = to_avro_values(test_dt)
        self.assertEqual(test_res, res)
        self.assertIsInstance(res, int)

    def test_list_to_str(self):
        uuid4_test = uuid4()
        test_list = ["a", "b", uuid4_test]
        res = to_avro_values(test_list)
        self.assertListEqual(list(map(str, test_list)), res)

    def test_dict_to_str(self):
        uuid4_test = uuid4()
        uuid4_test_key = uuid4()
        test_dict = {"a": "b", uuid4_test_key: uuid4_test}
        res = to_avro_values(test_dict)
        self.assertDictEqual({"a": "b", str(uuid4_test_key): str(uuid4_test)}, res)

    def test_nested_falttened(self):
        uuid4_test = uuid4()
        test_dict = {"a": {"b": {"c": "d", "e": ["a", "c", uuid4_test]}}}
        res = to_avro_values(test_dict)
        self.assertEqual(
            {"a": {"b": {"c": "d", "e": ["a", "c", str(uuid4_test)]}}}, res
        )
