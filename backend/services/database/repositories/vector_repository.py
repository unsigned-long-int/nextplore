from typing import List
from uuid import UUID
from sqlalchemy.engine import Row

from services.database.models import VectorORM
from services.database.dependencies import backend_session_scope


class VectorRepository:
    def get_integration_vectors(self, integration_ids: List[UUID]) -> List[Row]:
        if not integration_ids:
            return []
        
        with backend_session_scope() as scoped_session:
            vector_query = (
                scoped_session.query(
                    VectorORM.integration_id,
                    VectorORM.schema_name,
                    VectorORM.table_name,
                    VectorORM.table_meta,
                    VectorORM.vector
                )
                .filter(VectorORM.integration_id.in_(integration_ids))
            )

            return scoped_session.execute(vector_query).all()
