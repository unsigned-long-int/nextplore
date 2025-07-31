from uuid import UUID

from database.repositories import VectorRepository


async def delete_pg_vector_metadata(integration_id: UUID) -> None:
    vector_repo = VectorRepository()
    await vector_repo.delete_vector_meta(integration_id)
