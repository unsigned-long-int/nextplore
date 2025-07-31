from typing import Optional
from uuid import UUID

from shared.cache.client import BaseCache
from shared.identity_service.user_identity import UserIdentity


class IndentityServiceCache(BaseCache):
    def __init__(self):
        super().__init__(namespace='user_identity', version='v1')

    async def get_user_identity(self, tid: str, oid: str) -> Optional[UserIdentity]:
        raw = await self.get_raw(tid, oid)
        if not raw:
            return None
        return UserIdentity(
            organization_id=UUID(raw['organization_id']),
            user_id=UUID(raw['user_id'])
        )

    async def set_user_identity(self, tid: str, oid: str, identity: UserIdentity, ttl: int = 600):
        await self.set_raw(
            tid, oid,
            value={
                'organization_id': str(identity.organization_id),
                'user_id': str(identity.user_id)
            },
            ttl=ttl
        )

identity_cache_service = IndentityServiceCache()
