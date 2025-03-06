from sqlalchemy import create_engine
from pathlib import Path

from infrastructure.credentials_loader import load_credentials
from infrastructure.event_orchestration_service.event_orchestrator import (
    EventOrchestrator,
    handle_event
)

from infrastructure.manifest_loader import load_manifest
from infrastructure.open_ai_client_loader import load_open_ai_client
from infrastructure.ui_interface.cli import CLIParser
from infrastructure.storage.ingestion_service import (
    HDF5IngestionService,
    CSVIngestionService
)
from infrastructure.storage.retrieval_service import (
    HDF5RetrievalService,
    CSVRetrievalService
)
from infrastructure.storage.upsert_orchestration_service import (
    UpsertOrchestrationService,
    create_upsert_orchestration_service
)
from infrastructure.storage.database_inspection_service import (
    fetch_database_descriptor
)
from core.orm_factory import AIORMFactory


def main() -> None:
    event_orchestrator = EventOrchestrator()
    credentials = load_credentials()

    client = load_open_ai_client(api_key=credentials.openai_api_key)
    engine = create_engine(credentials.sql_connection_string)
    manifest = load_manifest(event_orchestrator)

    ingestion_service = CSVIngestionService(
        csv_path=Path(__file__).resolve().parent /
        'repositories' / 'vectors.csv'
    )

    retrieval_service = CSVRetrievalService(
        csv_path=Path(__file__).resolve().parent /
        'repositories' / 'vectors.csv'
    )

    ai_orm_factory = AIORMFactory(
        client=client,
        event_orchestrator=event_orchestrator,
        engine=engine,
        ingestion_service=ingestion_service,
        retrieval_service=retrieval_service
    )

    cli_parser = CLIParser(
        ai_orm_factory=ai_orm_factory,
        prog_name=manifest.prog_name,
        description=manifest.description,
        engine=engine
    )

    cli_parser.process_query(event_orchestrator)

    if event_orchestrator.queue:
        handle_event(
            event=event_orchestrator.queue.pop(0),
            event_orchestrator=event_orchestrator
        )


if __name__ == '__main__':
    main()
