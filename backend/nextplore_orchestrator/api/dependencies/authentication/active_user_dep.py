from fastapi import Depends

from api.context import set_current_identity
from nextplore_shared.identity_service.identity_model.user_identity import UserIdentity
from nextplore_shared.identity_service.resolver.resolve_user_identity import resolve_user_identity
from .azure_user_dep import get_azure_user


async def get_active_user(azure_user = Depends(get_azure_user)) -> UserIdentity:
    azure_tenant_id = azure_user.get('tid')
    azure_user_id = azure_user.get('oid')

    identity = await resolve_user_identity(azure_tenant_id, azure_user_id)
    set_current_identity(identity)
    return identity
