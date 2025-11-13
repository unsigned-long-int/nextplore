from typing import Optional
from uuid import UUID

from nextplore_sdk.cache.client.interface import Cache
from nextplore_orchestrator.api.context import UserIdentity


class IdentityCacheService:
    def __init__(self, cache: Cache):
        self.cache = cache

    async def get_user_identity(self, tid: str, oid: str) -> Optional[UserIdentity]:
        raw = await self.cache.get_raw(tid, oid)
        if not raw:
            return None
        return UserIdentity(
            organization_id=UUID(raw['organization_id']),
            user_id=UUID(raw['user_id'])
        )

    async def set_user_identity(self, tid: str, oid: str, identity: UserIdentity, ttl: int = 600):
        await self.cache.set_raw(
            tid, oid,
            value={
                'organization_id': str(identity.organization_id),
                'user_id': str(identity.user_id)
            },
            ttl=ttl
        )
