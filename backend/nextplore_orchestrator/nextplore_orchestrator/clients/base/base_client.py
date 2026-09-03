import json
from datetime import date, datetime
from enum import Enum
from typing import Any
from uuid import UUID

import httpx
from pydantic import BaseModel, SecretStr

from nextplore_orchestrator.api.context import get_current_identity
import os

_INTERNAL_TOKEN = os.environ["INTERNAL_SERVICE_TOKEN"]

class PayloadEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, SecretStr):
            return obj.get_secret_value()
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)


class BaseServiceClient:
    def __init__(self, base_url: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(read=60.0, write=20.0, connect=3.0, pool=5.0),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )

    async def post(
        self, path: str, payload: BaseModel, headers: dict[str, Any] | None = None
    ):
        adapted_headers = self._inject_identity_headers(headers)
        response = await self.client.post(
            path, json=self._serialize(payload), headers=adapted_headers
        )
        response.raise_for_status()
        return response

    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
    ):
        adapted_headers = self._inject_identity_headers(headers)
        response = await self.client.get(path, params=params, headers=adapted_headers)
        return response

    async def delete(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
    ):
        adapted_headers = self._inject_identity_headers(headers)
        response = await self.client.delete(
            path, params=params, headers=adapted_headers
        )
        return response

    async def put(
        self, path: str, payload: BaseModel, headers: dict[str, Any] | None = None
    ):
        adapted_headers = self._inject_identity_headers(headers)
        response = await self.client.put(
            path, json=self._serialize(payload), headers=adapted_headers
        )
        return response

    async def patch(
        self, path: str, payload: BaseModel, headers: dict[str, Any] | None = None
    ):
        adapted_headers = self._inject_identity_headers(headers)
        response = await self.client.patch(
            path, json=self._serialize(payload), headers=adapted_headers
        )
        return response

    async def close(self) -> None:
        await self.client.aclose()

    @staticmethod
    def _inject_identity_headers(
            headers: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        identity = get_current_identity()
        base_headers = headers.copy() if headers else {}
        base_headers.setdefault("x-user-id", str(identity.user_id))
        base_headers.setdefault("x-org-id", str(identity.organization_id))
        base_headers.setdefault("x-internal-token", _INTERNAL_TOKEN)
        return base_headers

    @staticmethod
    def _serialize(payload: BaseModel | dict[str, Any]) -> dict[str, Any]:
        raw = payload.model_dump() if isinstance(payload, BaseModel) else payload
        return json.loads(json.dumps(raw, cls=PayloadEncoder))
