from uuid import UUID
from typing import Dict, Any, List


from svc_vector_contracts.models import VectorMetadata, VectorSearchResult
from svc_llm_inference_contracts.models import LlmOutputSpecs, IntegrationEntry, SchemaEntry
from nextplore_orchestrator.domain.models import (
    Organization,
    User,
    OrmMetadata,
    VectorNeighbour,
    RagContext
)


def organization_from_dto(user: Dict[str, Any]) -> Organization:
    name = user.get('name')
    azure_tenant_id = user.get('tid')
    email = user.get('preferred_username')
    domain = email.split('@')[-1]

    return Organization(
        azure_tenant_id=azure_tenant_id,
        name=name,
        domain=domain
    )


def user_from_dto(user: Dict[str, Any], organization_id: UUID) -> User:
    name = user.get('name')
    azure_user_id = user.get('oid')
    sub = user.get('sub')
    email = user.get('preferred_username')
    roles = user.get('roles', [])

    return User(
        azure_user_id=azure_user_id,
        email=email,
        name=name,
        organization_id=organization_id,
        sub=sub,
        role=','.join(roles) if roles else None
    )


def vector_neighbours_from_dto(vector_hits_meta: List[VectorMetadata], vector_hits: List[VectorSearchResult]) -> List[VectorNeighbour]:

    vector_meta_by_id = {vector_meta.vector_id: vector_meta for vector_meta in vector_hits_meta}
    vector_hits_by_id = {vector_hit.vector_id: vector_hit for vector_hit in vector_hits}

    return [
        VectorNeighbour(
            id=vid,
            score=vector_hits_by_id[vid].score,
            orm_metadata=OrmMetadata(
                integration_id=vector_meta_by_id[vid].integration_id,
                schema_name=vector_meta_by_id[vid].schema_name,
                table_name=vector_meta_by_id[vid].table_name,
                column_names=vector_meta_by_id[vid].table_metadata.column_names
            )
        )
        for vid in vector_hits_by_id.keys()
    ]


def llm_output_specs_dto_from_rag_context(rag_context: RagContext) -> LlmOutputSpecs:
    return LlmOutputSpecs(
        integration_registry_repr=rag_context.integration_registry_repr,
        integrations_enum=rag_context.integrations_enum,
        schemas_enum=rag_context.schemas_enum,
        tables_enum=rag_context.tables_enum,
        columns_enum=rag_context.columns_enum,
        filter_op_enum=rag_context.filter_op_enum,
        agg_funcs_enum=rag_context.agg_funcs_enum,
        table_columns_registry={
            integration_id: IntegrationEntry(schemas={
                schema_name: SchemaEntry(tables=tables)
                for schema_name, tables in schemas.items()
            })
            for integration_id, schemas in rag_context.table_columns_registry.items()
        }
    )