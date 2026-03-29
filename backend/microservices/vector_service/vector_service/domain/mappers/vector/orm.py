import json

from vector_service.database.models import VectorORM
from vector_service.domain.models.vector import VectorProfile


def orm_to_domain_vector_profile(vector_orm: VectorORM) -> VectorProfile:
    return VectorProfile(
        datastore_id=vector_orm.datastore_id,
        schema_name=vector_orm.schema_name,
        table_name=vector_orm.table_name,
        table_meta=json.loads(vector_orm.table_meta)
    )
