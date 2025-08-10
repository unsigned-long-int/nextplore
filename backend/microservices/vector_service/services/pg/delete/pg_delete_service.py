from uuid import UUID

from nextplore_shared.database.dependencies.database_backend_connector import DatabaseBackendConnector
from database.repositories import VectorRepository


async def delete_pg_vector_metadata(
    connector: DatabaseBackendConnector,
    organization_id: UUID, 
    user_id: UUID, 
    integration_id: UUID
) -> None:
    vector_repo = VectorRepository(connector)
    await vector_repo.delete_vector_meta(
        organization_id=organization_id, 
        user_id=user_id,
        integration_id=integration_id
    )
