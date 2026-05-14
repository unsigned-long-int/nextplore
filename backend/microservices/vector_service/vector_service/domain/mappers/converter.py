import json
from typing import List

from qdrant_client.http.models import FieldCondition, MatchValue
from svc_vector_contracts.models import SemanticCacheEntry, SemanticCacheLookupQuery

from vector_service.database.models import VectorORM
from vector_service.domain.models import VectorProfile, SemanticCacheMeta


def orm_to_domain_vector_profile(vector_orm: VectorORM) -> VectorProfile:
    return VectorProfile(
        datastore_id=vector_orm.datastore_id,
        schema_name=vector_orm.schema_name,
        table_name=vector_orm.table_name,
        table_meta=json.loads(vector_orm.table_meta)
    )


def semantic_cache_meta_from_dto(entry: SemanticCacheEntry) -> SemanticCacheMeta:
    return SemanticCacheMeta(
        embedding=entry.embedding,
        extra={
            'json_payload': entry.json_payload,
            'expires_at': entry.expires_at,
            'provider': entry.provider,
            'model_id': entry.model_id,
            'model_ref_id': entry.model_ref_id
        }
    )

def refine_filters_from_dto(lookup_query: SemanticCacheLookupQuery) -> List[FieldCondition]:
    filters = []
    if lookup_query.provider:
        filters.append(FieldCondition(key='provider', match=MatchValue(value=lookup_query.provider)))
    if lookup_query.model_id:
        filters.append(FieldCondition(key='model_id', match=MatchValue(value=lookup_query.model_id)))
    if lookup_query.model_ref_id is not None:
        filters.append(FieldCondition(key='model_ref_id', match=MatchValue(value=str(lookup_query.model_ref_id))))
    return filters