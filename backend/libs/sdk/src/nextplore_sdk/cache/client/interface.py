import logging
from typing import Any, Protocol, TypeVar, runtime_checkable
from uuid import UUID

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


@runtime_checkable
class Cache(Protocol):
    async def get_one(self, *parts: str | UUID, model: type[T]) -> T | None: ...
    async def set_one(
        self, *parts: str | UUID, value: BaseModel, ttl: int | None = None
    ): ...
    async def get_many(self, *parts: str | UUID, model: type[T]) -> list[T] | None: ...
    async def set_many(
        self, *parts: str | UUID, value: list[BaseModel], ttl: int | None = None
    ): ...
    async def get_raw(self, *parts: str | UUID) -> dict[str, Any] | None: ...
    async def set_raw(
        self, *parts: str | UUID, value: dict[str, Any], ttl: int | None = None
    ): ...
    async def delete(self, *parts: str | UUID): ...
    async def delete_by_prefix(
        self, *prefix_parts: str | UUID, batch_size: int = 100
    ) -> None: ...
