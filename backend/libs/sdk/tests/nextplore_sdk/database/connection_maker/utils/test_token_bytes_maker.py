import struct
import unittest

from nextplore_sdk.database.connection_maker.utils.token_bytes_maker import (
    make_token_bytes,
)


class TestMakeTokenBytes(unittest.TestCase):
    def _expected_payload(self, s: str) -> bytes:
        out = bytearray()
        for b in s.encode("utf-8"):
            out.append(b)
            out.append(0)
        return bytes(out)

    def _assert_token_structure(self, token: str):
        result = make_token_bytes(token)

        self.assertGreaterEqual(len(result), 4)
        (payload_len,) = struct.unpack("=i", result[:4])
        payload = result[4:]

        self.assertEqual(payload_len, len(payload))

        expected = self._expected_payload(token)
        self.assertEqual(payload, expected)

    def test_empty_string(self):
        self._assert_token_structure("")

    def test_ascii(self):
        self._assert_token_structure("ABC")

    def test_unicode_multibyte(self):
        self._assert_token_structure("Ø")

    def test_mixed_ascii_and_unicode(self):
        self._assert_token_structure("Hi-Ø")

    def test_known_bytes_exact(self):
        token = "AB"
        result = make_token_bytes(token)
        (payload_len,) = struct.unpack("=i", result[:4])
        payload = result[4:]
        self.assertEqual(payload_len, 4)
        self.assertEqual(payload, b"A\x00B\x00")
