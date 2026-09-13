from slowapi import Limiter
from slowapi.util import get_remote_address

from nextplore_orchestrator.api.context import (
    UserIdentityContextError,
    get_current_identity,
)

limiter = Limiter(key_func=get_remote_address)

def get_identity_key(request) -> str:
    try:
        identity = get_current_identity()
    except UserIdentityContextError:
        return get_remote_address(request)
    return f"org:{identity.organization_id}|user:{identity.user_id}"
