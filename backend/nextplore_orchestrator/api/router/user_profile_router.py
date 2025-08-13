from sqlalchemy import select
from fastapi import APIRouter, Depends

from nextplore_sdk.database.dependencies.database_backend_connector import DatabaseBackendConnector
from nextplore_sdk.contracts.nextplore_orchestrator_service.user_profile import UserProfile
from cache.orchestrator_cache import OrchestratorCacheService
from database.models.organization_orm import OrganizationORM
from database.models.user_orm import UserORM
from api.dependencies.cache import get_orchestrator_cache_service
from api.dependencies.authentication import get_azure_user


router = APIRouter()

@router.get('', response_model=UserProfile)
async def get_user_profile(
    user=Depends(get_azure_user),
    cache_service: OrchestratorCacheService = Depends(get_orchestrator_cache_service)
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

    cached = await cache_service.get_user_profile(
        azure_tenant_id,
        azure_user_id
    )
    if cached:
        return cached

    database_backend_connector = DatabaseBackendConnector()
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

        response = UserProfile(
            id=user.id,
            email=user.email,
            name=user.name,
            organization=org.name,
            organization_id=org.id
        )

        await cache_service.set_user_profile(
            azure_tenant_id,
            azure_user_id,
            response=response,
            ttl=300
        )

        return response
    