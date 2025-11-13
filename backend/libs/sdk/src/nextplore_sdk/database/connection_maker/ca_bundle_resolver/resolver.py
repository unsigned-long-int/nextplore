import os
import ssl
import certifi
from typing import Optional


def resolve_ca_bundle() -> Optional[str]:
    if ca_bundle := os.getenv('NEXTPLORE_CA_BUNDLE'):
        return ca_bundle

    v = ssl.get_default_verify_paths()
    if v.cafile and os.path.isfile(v.cafile):
        return v.cafile

    return certifi.where()
