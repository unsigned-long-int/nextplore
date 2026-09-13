import ipaddress
import socket
from collections.abc import Callable
from urllib.parse import urlparse

Resolver = Callable[[str], list[str]]


class UnsafeApiBaseError(Exception):
    pass


def _default_resolve(hostname: str) -> list[str]:
    return [sockaddr[0] for *_, sockaddr in socket.getaddrinfo(hostname, None)]


def assert_safe_api_base(url: str, resolve: Resolver = _default_resolve) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise UnsafeApiBaseError(f"api_base must use https, got {url!r}")
    if not parsed.hostname:
        raise UnsafeApiBaseError(f"api_base must have hostname {url!r}")

    try:
        resolved_ips = resolve(parsed.hostname)
    except socket.gaierror as e:
        raise UnsafeApiBaseError(f"api_base host could not be resolved: {url!r}") from e

    for raw_ip in resolved_ips:
        ip = ipaddress.ip_address(raw_ip)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise UnsafeApiBaseError(
                f"api_base resolves to a non-public address({ip}): {url!r}"
            )
