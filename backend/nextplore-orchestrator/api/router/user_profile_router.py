from sqlalchemy import select
from fastapi import APIRouter, Depends

from shared.database.dependencies import DatabaseBackendConnector
from shared.database.models import OrganizationORM, UserORM
from api.dependencies.authentication import get_azure_user
from api.models import UserProfile

router = APIRouter()

@router.get('', response_model=UserProfile)
async def get_user_profile(
    user=Depends(get_azure_user)
) -> UserProfile:
    email = user.get('preferred_username')
    if not email:
        raise ValueError('preferred_username claim is missing')

    database_backend_connector = DatabaseBackendConnector()
    
    name = user.get('name')
    sub = user.get('sub')
    roles = user.get('roles', [])
    azure_tenant_id = user.get('tid')
    azure_user_id = user.get('oid')
    domain = email.split('@')[-1]

    async with database_backend_connector.session_scope() as scoped_session:
        result = await scoped_session.execute(
            select(OrganizationORM)
            .where(OrganizationORM.azure_tenant_id==azure_tenant_id)
        )
        org = result.scalar_one_or_none()
        if not org:
            org = OrganizationORM(
                azure_tenant_id=azure_tenant_id,
                name=domain,
                domain=domain,
                plan='standard'
            )
            scoped_session.add(org)
            scoped_session.flush()

        result = await scoped_session.execute(
            select(UserORM)
            .where(UserORM.azure_user_id == azure_user_id)
            .where(UserORM.organization_id == org.id)
        )
        user = result.scalar_one_or_none()
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
    