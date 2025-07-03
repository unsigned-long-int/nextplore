from openai import OpenAI
from uuid import UUID

from services.settings import settings
from services.credentials_loader import load_credentials
from services.open_ai_client_loader import load_open_ai_client
from services.sql_connection_service import fetch_engine
from core.database.inspection import inspect_integration_registry
from core.database.filter.logic import AlwaysTrueSpec
from core.database.vectors_ingestion import (
    IngestionServiceProtocol,
    PgVectorIngestionService
)
from .upsert_service import UpsertService


def create_upsert_orchestration_service(
        client: OpenAI,
        ingestion_service: IngestionServiceProtocol,
        integration_id: UUID
) -> UpsertService:
    integration_registry = inspect_integration_registry(
        integration_ids=[integration_id],
        integration_spec=AlwaysTrueSpec(),
        schema_spec=AlwaysTrueSpec(),
        table_spec=AlwaysTrueSpec()
    )

    upsert_service = UpsertService(
        client=client,
        integration_registry=integration_registry,
        ingestion_service=ingestion_service
    )

    return upsert_service


def upsert_metadata(integration_id: UUID) -> None:
    credentials = load_credentials()
    client = load_open_ai_client(credentials.openai_api_key)
    engine = fetch_engine(settings.DATABASE_URL)
    ingestor = PgVectorIngestionService(engine)
    upsert_orchestration_service = create_upsert_orchestration_service(
        client=client,
        ingestion_service=ingestor,
        integration_id=integration_id
    )
    upsert_orchestration_service.upsert_storage()
