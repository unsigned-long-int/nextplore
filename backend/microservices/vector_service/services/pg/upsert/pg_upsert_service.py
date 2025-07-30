from typing import List

from database.repositories import VectorRepository
from database.models import VectorORM


async def upsert_pg_vector_metadata(vectors_orm: List[VectorORM]) -> None:
    vector_repo = VectorRepository()
    await vector_repo.upsert_vector_meta(vectors_orm)
