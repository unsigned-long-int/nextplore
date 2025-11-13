from uuid import UUID
from typing import Dict, Any

from nextplore_orchestrator.domain.models import Organization, User


def organization_from_dto(user: Dict[str, Any]) -> Organization:
    name = user.get('name')
    azure_tenant_id = user.get('tid')
    email = user.get('preferred_username')
    domain = email.split('@')[-1]

    return Organization(
        azure_tenant_id=azure_tenant_id,
        name=name,
        domain=domain
    )


def user_from_dto(user: Dict[str, Any], organization_id: UUID) -> User:
    name = user.get('name')
    azure_user_id = user.get('oid')
    sub = user.get('sub')
    email = user.get('preferred_username')
    roles = user.get('roles', [])

    return User(
        azure_user_id=azure_user_id,
        email=email,
        name=name,
        organization_id=organization_id,
        sub=sub,
        role=','.join(roles) if roles else None
    )
