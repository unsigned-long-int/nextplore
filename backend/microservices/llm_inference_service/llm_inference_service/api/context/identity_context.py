from typing import Optional
from contextvars import ContextVar

from .user_identity import UserIdentity
from .exc import UserIdentityContextError

identity_context: Optional[ContextVar[UserIdentity]] = ContextVar('identity_context', default=None)


def set_current_identity(identity: UserIdentity):
    identity_context.set(identity)


def get_current_identity() -> Optional[UserIdentity]:
    if (user_identity := identity_context.get()) is not None:
        return user_identity
    raise UserIdentityContextError('User identity not found in context')
