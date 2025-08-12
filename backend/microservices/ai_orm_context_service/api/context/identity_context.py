from typing import Optional
from contextvars import ContextVar

from nextplore_sdk.identity_service.identity_model.user_identity import UserIdentity

identity_context: Optional[ContextVar[UserIdentity]] = ContextVar('identity_context', default=None)

def set_current_identity(identity: UserIdentity):
    identity_context.set(identity)

def get_current_identity() -> Optional[UserIdentity]:
    return identity_context.get()
