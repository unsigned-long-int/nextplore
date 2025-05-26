from openai import OpenAI
from sqlalchemy import Engine

from services.event_orchestration_service.event_orchestrator import EventOrchestrator
from services.storage.user_database_inspector import fetch_database_descriptor
from services.storage.database_metadata_ingestor import IngestionServiceProtocol

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
