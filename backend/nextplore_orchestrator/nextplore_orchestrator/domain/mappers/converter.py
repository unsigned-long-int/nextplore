from uuid import UUID
from typing import Dict, Any, List, Optional

from nextplore_orchestrator.api.models.ai_query_request import AIQueryRequest
from nextplore_orchestrator.domain.models import (
    Organization,
    User,
    OrmMetadata,
    VectorNeighbour,
    RagContext,
    LlmSpec,
    OnboardingRequest
)
from nextplore_orchestrator.database.models import OnboardingRequestORM, OrganizationORM

from svc_nextplore_orchestrator_contracts.models import LlmProfile, LlmSource, RegisterRequest
from svc_integration_contracts.models import UserLlmProfile
from svc_vector_contracts.models import VectorMetadata, VectorSearchResult
from svc_llm_inference_contracts.models import LlmOutputSpecs, DataStoreEntry, SchemaEntry, ModelInfo, UserLlmConfig


def organization_from_dto(
    user: Dict[str, Any],
    onboarding_id: UUID
) -> Organization:
    name = user.get('name')
    azure_tenant_id = user.get('tid')
    email = user.get('preferred_username')
    domain = email.split('@')[-1]

    return Organization(
        azure_tenant_id=azure_tenant_id,
        name=name,
        domain=domain,
        onboarding_request_id=onboarding_id
    )


def organization_from_orm(organization: OrganizationORM) -> Organization:
    return Organization(
        name=organization.name,
        domain=organization.domain,
        azure_tenant_id=organization.azure_tenant_id,
        plan=organization.plan,
        status=organization.status,
        id=organization.id,
        onboarding_request_id=organization.onboarding_request_id,
        activated_at=organization.activated_at,
        suspended_at=organization.suspended_at,
        suspend_reason=organization.suspend_reason,
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
                datastore_id=vector_meta_by_id[vid].datastore_id,
                schema_name=vector_meta_by_id[vid].schema_name,
                table_name=vector_meta_by_id[vid].table_name,
                column_names=vector_meta_by_id[vid].table_metadata.column_names
            )
        )
        for vid in vector_hits_by_id.keys()
    ]


def llm_output_specs_dto_from_rag_context(rag_context: RagContext) -> LlmOutputSpecs:
    return LlmOutputSpecs(
        datastore_registry_repr=rag_context.datastore_registry_repr,
        datastores_enum=rag_context.datastores_enum,
        schemas_enum=rag_context.schemas_enum,
        tables_enum=rag_context.tables_enum,
        columns_enum=rag_context.columns_enum,
        filter_op_enum=rag_context.filter_op_enum,
        agg_funcs_enum=rag_context.agg_funcs_enum,
        table_columns_registry={
            datastore_id: DataStoreEntry(schemas={
                schema_name: SchemaEntry(tables=tables)
                for schema_name, tables in schemas.items()
            })
            for datastore_id, schemas in rag_context.table_columns_registry.items()
        }
    )

def llm_profile_from_platform_model(platform_model: ModelInfo) -> LlmProfile:
    return LlmProfile(
        source=LlmSource.platform,
        provider=platform_model.provider,
        label=platform_model.label,
        tags=platform_model.tags,
        model_id=platform_model.model_id,
        model_ref_id=None
    )


def llm_profile_from_user_model(user_model: UserLlmProfile) -> LlmProfile:
    return LlmProfile(
        source=LlmSource.user,
        provider='custom',
        label=user_model.label,
        tags=[],
        model_id=user_model.model_id,
        model_ref_id=user_model.model_ref_id
    )


def base_llm_spec_from_query_request(query_request: AIQueryRequest) -> LlmSpec:
    return LlmSpec(
        provider=query_request.provider,
        model_id=query_request.model_id,
        prompt=query_request.prompt
    )

def user_llm_config_from_llm_spec(llm_spec: LlmSpec) -> Optional[UserLlmConfig]:
    if llm_spec.user_llm_config:
        return UserLlmConfig(
            api_base=llm_spec.user_llm_config.api_base,
            connection_params=llm_spec.user_llm_config.connection_params,
            max_tokens=llm_spec.user_llm_config.max_tokens
        )
    return None


def onboarding_request_from_orm(req: OnboardingRequestORM) -> OnboardingRequest:
    return OnboardingRequest(
        company_name=req.company_name,
        email_domain=req.domain,
        contact_email=req.contact_email,
        plan=req.plan,
        email_verified=req.email_verified,
        status=req.status,
        id=req.id,
        verification_token=req.verification_token,
        verified_at=req.verified_at,
        reviewed_by=req.reviewed_by,
        review_note=req.review_note,
        reviewed_at=req.reviewed_at,
        outbox_mail_id=req.outbox_mail_id,
        verification_token_expires_at=req.verification_token_expires_at,
    )

def onboarding_request_from_dto(req: RegisterRequest) -> OnboardingRequest:
    email_domain = str(req.contact_email).split('@')[1].lower()
    return OnboardingRequest(
        company_name=req.company_name,
        contact_email=str(req.contact_email),
        email_domain=email_domain,
        plan=req.plan
    )