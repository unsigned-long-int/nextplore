from contextvars import ContextVar

from .exc import UserIdentityContextError
from .user_identity import UserIdentity

identity_context: ContextVar[UserIdentity] | None = ContextVar(
    "identity_context", default=None
)


def set_current_identity(identity: UserIdentity):
    identity_context.set(identity)


def get_current_identity() -> UserIdentity | None:
    if (user_identity := identity_context.get()) is not None:
        return user_identity
    raise UserIdentityContextError("User identity not found in context")
