from openai import OpenAI
from sqlalchemy import Engine

from services.credentials_loader import load_credentials
from services.open_ai_client_loader import load_open_ai_client
from services.sql_connection_service import fetch_engine
from services.event_orchestration_service.event_orchestrator import EventOrchestrator
from core.database.user_database_inspector import fetch_database_descriptor
from core.database.database_metadata_ingestor import (
    IngestionServiceProtocol,
    PgVectorIngestionService
)
from .upsert_orchestration_service import UpsertOrchestrationService


def create_upsert_orchestration_service(
        client: OpenAI,
        event_orchestrator: EventOrchestrator,
        engine: Engine,
        ingestion_service: IngestionServiceProtocol
) -> UpsertOrchestrationService:
    database_descriptor = fetch_database_descriptor(
        event_orchestrator=event_orchestrator,
        engine=engine
    )

    upsert_orchestration_service = UpsertOrchestrationService(
        client=client,
        database_descriptor=database_descriptor,
        ingestion_service=ingestion_service
    )

    return upsert_orchestration_service


def upsert_metadata(connection_string: str) -> None:
    event_orchestrator = EventOrchestrator()
    credentials = load_credentials()
    client = load_open_ai_client(credentials.openai_api_key, event_orchestrator=event_orchestrator)
    engine = fetch_engine(connection_string)
    ingestor = PgVectorIngestionService(engine)
    upsert_orchestration_service = create_upsert_orchestration_service(
        client=client,
        event_orchestrator=event_orchestrator,
        engine=engine,
        ingestion_service=ingestor
    )
    upsert_orchestration_service.upsert_storage()
