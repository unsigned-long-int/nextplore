from fastapi import APIRouter, Depends

from shared.database.dependencies import backend_session_scope
from shared.database.models import OrganizationORM, UserORM
from internal_services.authentication import get_active_user
from api.models import UserProfile

router = APIRouter()

@router.get('', response_model=UserProfile)
def get_user_profile(
    user=Depends(get_active_user)
) -> UserProfile:
    email = user.get('preferred_username')
    if not email:
        raise ValueError('preferred_username claim is missing')

    name = user.get('name')
    sub = user.get('sub')
    roles = user.get('roles', [])
    azure_tenant_id = user.get('tid')
    azure_user_id = user.get('oid')
    domain = email.split('@')[-1]

    with backend_session_scope() as scoped_session:
        org = scoped_session.query(OrganizationORM).filter_by(azure_tenant_id=azure_tenant_id).first()
        if not org:
            org = OrganizationORM(
                azure_tenant_id=azure_tenant_id,
                name=domain,
                domain=domain,
                plan='standard'
            )
            scoped_session.add(org)
            scoped_session.flush()

        user = (
            scoped_session.query(UserORM)
            .filter_by(azure_user_id=azure_user_id, organization_id=org.id)
            .first()
        )
        if not user:
            user = UserORM(
                azure_user_id=azure_user_id,
                email=email,
                name=name,
                organization_id=org.id,
                sub=sub,
                role=','.join(roles) if roles else None,
            )
            scoped_session.add(user)
            scoped_session.flush()

        return UserProfile(
            id=user.id,
            email=user.email,
            name=user.name,
            organization=org.name,
            organization_id=org.id
        )
    