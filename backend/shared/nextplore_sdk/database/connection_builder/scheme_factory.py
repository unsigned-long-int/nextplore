from .scheme_registry import SCHEME_REGISTRY


def dispatch_scheme(service_type: str) -> str:
    scheme = SCHEME_REGISTRY.get(service_type)
    if not scheme:
        raise ValueError(f'Unsupported service type: {service_type}')
    return scheme