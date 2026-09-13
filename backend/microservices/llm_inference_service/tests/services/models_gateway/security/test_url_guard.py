import unittest

from llm_inference_service.services.models_gateway.security.url_guard import (
    UnsafeApiBaseError,
    assert_safe_api_base,
)


def resolver(ip: str):
    return lambda hostname: [ip]


class TestAssertSafeApiBase(unittest.TestCase):
    def test_allows_a_public_https_host(self):
        assert_safe_api_base(
            "https://my-endpoint.com/v1", resolve=resolver("93.184.216.34")
        )

    def test_rejects_http(self):
        with self.assertRaises(UnsafeApiBaseError):
            assert_safe_api_base(
                "http://my-endpoint.com/v1", resolve=resolver("93.184.216.34")
            )

    def test_rejects_private_address(self):
        with self.assertRaises(UnsafeApiBaseError):
            assert_safe_api_base(
                "https://internal.svc/v1", resolve=resolver("10.0.0.5")
            )

    def test_rejects_loopback(self):
        with self.assertRaises(UnsafeApiBaseError):
            assert_safe_api_base("https://localhost/v1", resolve=resolver("127.0.0.1"))

    def test_rejects_link_local_metadata_endpoint(self):
        with self.assertRaises(UnsafeApiBaseError):
            assert_safe_api_base(
                "https://metadata/v1", resolve=resolver("169.254.169.254")
            )

    def test_rejects_unresolvable_host(self):
        import socket

        def raises(_hostname):
            raise socket.gaierror("nope")

        with self.assertRaises(UnsafeApiBaseError):
            assert_safe_api_base("https://nowhere.invalid/v1", resolve=raises)
