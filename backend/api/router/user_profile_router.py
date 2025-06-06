import uuid
from fastapi import APIRouter, Depends

from services.database.dependencies import backend_session_scope
from services.database.models import Organization, User
from services.authentication import get_active_user
from api.models import UserProfile

router = APIRouter()

@router.get('', response_model=UserProfile)
def get_user_profile(
    user=Depends(get_active_user)
) -> UserProfile:
    print('geceiving data')
    email = user.get("preferred_username")
    print(email)
    if not email:
        raise ValueError("preferred_username claim is missing")

    name = user.get("name")
    sub = user.get("sub")
    roles = user.get("roles", [])
    domain = email.split("@")[-1]

    with backend_session_scope() as scoped_session:
        org = scoped_session.query(Organization).filter_by(domain=domain).first()
        if not org:
            org = Organization(
                id=uuid.uuid4(),
                name=domain,
                domain=domain,
                plan="standard",
            )
            scoped_session.add(org)
            scoped_session.flush()

        user = (
            scoped_session.query(User)
            .filter_by(sub=sub, organization_id=org.id)
            .first()
        )
        if not user:
            user = User(
                id=uuid.uuid4(),
                email=email,
                name=name,
                organization_id=org.id,
                sub=sub,
                role=",".join(roles) if roles else None,
            )
            scoped_session.add(user)
            scoped_session.flush()

        return UserProfile(
            id=user.id,
            email=user.email,
            name=user.name,
            organization=org.name,
            organization_id=org.id,
        )