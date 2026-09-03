from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Iterator
from uuid import UUID


class UserIdentityContextError(Exception):
    pass


@dataclass(frozen=True)
class UserIdentity:
    organization_id: UUID
    user_id: UUID


identity_context: ContextVar[UserIdentity | None] = ContextVar(
    "identity_context", default=None
)


def set_current_identity(
    identity: UserIdentity | None,
) -> Token[UserIdentity | None]:
    return identity_context.set(identity)


def get_current_identity() -> UserIdentity:
    identity = identity_context.get()
    if identity is None:
        raise UserIdentityContextError("User identity not found in context")
    return identity


@contextmanager
def current_identity(identity: UserIdentity) -> Iterator[UserIdentity]:
    token = set_current_identity(identity)
    try:
        yield identity
    finally:
        identity_context.reset(token)