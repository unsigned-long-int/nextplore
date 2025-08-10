from uuid import UUID
from typing import List

from database.repositories import VectorRepository
from nextplore_shared.database.dependencies.database_backend_connector import DatabaseBackendConnector
from nextplore_shared.database.models.vector_orm import VectorORM


async def upsert_pg_vector_metadata(
    connector: DatabaseBackendConnector, 
    organization_id: UUID, 
    user_id: UUID, 
    vectors_orm: List[VectorORM]
) -> None:
    vector_repo = VectorRepository(connector)
    await vector_repo.upsert_vector_meta(
        organization_id=organization_id, 
        user_id=user_id, 
        vectors_orm=vectors_orm
    )
