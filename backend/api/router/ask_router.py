from fastapi import APIRouter
from typing import Callable
from api.models import AskRequest, AskResponse
from core.orm_factory import AIORMFactory
from sqlalchemy import create_engine
from pathlib import Path

from infrastructure.credentials_loader import load_credentials
from infrastructure.event_orchestration_service.event_orchestrator import (
    EventOrchestrator
)
from infrastructure.manifest_loader import load_manifest
from infrastructure.open_ai_client_loader import load_open_ai_client
from infrastructure.storage.ingestion_service import (
    CSVIngestionService
)
from infrastructure.storage.retrieval_service import (
    CSVRetrievalService
)
from core.orm_factory import generate_orm_statement
from sqlalchemy.orm import sessionmaker
from infrastructure.sql_connection_service import fetch_engine, fetch_session_maker, session_scope


event_orchestrator = EventOrchestrator()
credentials = load_credentials()

client = load_open_ai_client(
    api_key=credentials.openai_api_key, 
    event_orchestrator=event_orchestrator
    )
engine = fetch_engine(credentials.sql_connection_string)
manifest = load_manifest(event_orchestrator)


retrieval_service = CSVRetrievalService(
    csv_path=Path(__file__).resolve().parent.parent.parent /
    'repositories' / 'vectors.csv'
)

ingestion_service = CSVIngestionService(
    csv_path=Path(__file__).resolve().parent.parent.parent /
    'repositories' / 'vectors.csv'
)

ai_orm_factory = AIORMFactory(
    client=client,
    event_orchestrator=event_orchestrator,
    engine=engine,
    ingestion_service=ingestion_service,
    retrieval_service=retrieval_service
)
router = APIRouter()

@router.post("/", response_model=AskResponse)
def ask_query(request: AskRequest):
    orm_request = ai_orm_factory.retrieve_orm_model(request.prompt)
    session_factory = fetch_session_maker(engine)

    with session_scope(session_factory) as session:
        statement = generate_orm_statement(model=orm_request.orm_model, filters=orm_request.filters)
        sample = session.execute(statement).scalars().all()
        print(sample)
        #session.execute()
        #query_request = session.query(orm_model)
        #sample = query_request.all()
        if sample:
            headers = sample[0].__table__.columns.keys()
            return AskResponse(
                sql=str(statement),
                data=[{column: str(getattr(row, column))
                            for column in headers} for row in sample]
            )
        return AskResponse(
            sql=str(statement),
            data=[]
        )