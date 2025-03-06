import json
import pandas as pd

from sqlalchemy import Engine, inspect
from queue import Queue
from dataclasses import dataclass
from openai import OpenAI
from typing import List, Optional, Callable

from infrastructure.cosine_similarity import cosine_similarity
from infrastructure.storage.database_inspection_service import DatabaseInspectionFilter
from infrastructure.storage.upsert_orchestration_service import UpsertOrchestrationService
from infrastructure.storage.ingestion_service import IngestionServiceProtocol
from infrastructure.storage.retrieval_service import RetrievalServiceProtocol
from infrastructure.storage.database_inspection_service import fetch_database_descriptor
from infrastructure.vector_generation_service import VectorGenerator
from infrastructure.event_orchestration_service.event_orchestrator import EventOrchestrator
from core.context_retriever import retrieve_contextual_vector_matrix
from .orm_meta import generate_orm_class


@dataclass
class AIORMFactory:
    client: OpenAI
    event_orchestrator: EventOrchestrator
    engine: Engine
    ingestion_service: IngestionServiceProtocol
    retrieval_service: RetrievalServiceProtocol
    upsert_factory_callback: Optional[Callable] = None

    def retrieve_orm_model(self, query: str, progress_queue: Queue) -> type:
        if self.upsert_factory_callback:
            self._upsert_meta(progress_queue)

        orm_vectors = self._retrieve_meta(progress_queue)
        query_vector = self._vectorize_query(query, progress_queue)

        contextual_vector_matrix = retrieve_contextual_vector_matrix(
            query_vector=query_vector,
            orm_vectors=orm_vectors,
            progress_queue=progress_queue
        )
        database_inspection_filters = [
            DatabaseInspectionFilter(
                schema_name=schema_name,
                table_name=table_name,
            ) for schema_name, table_name, *_ in contextual_vector_matrix
        ]

        database_descriptor = fetch_database_descriptor(
            event_orchestrator=self.event_orchestrator,
            engine=self.engine,
            database_inspection_filters=database_inspection_filters
        )

        progress_queue.put('searching for most suitable orm model...')
        tools = [{'type': 'function',
                  'function': {
                      'name': 'generate_orm_class',
                      'description': f'Function: {generate_orm_class.__doc__}.',
                      'parameters': {
                          'type': 'object',
                          'properties': {
                              'schema_name': {
                                  'type': 'string',
                                  'description': f'delivers the name of the schema from Metadata: {repr(database_descriptor)}',
                                  'enum': database_descriptor.schema_name_enum
                              },
                              'class_name': {
                                  'type': 'string',
                                  'description': f'delivers ORM class name for chosen table, each first letter to be capitalized.'
                              },
                              'table_name': {
                                  'type': 'string',
                                  'description': f'delivers the name of table for respective schema from Metadata: {repr(database_descriptor)}',
                                  'enum': database_descriptor.table_name_enum
                              },
                              'column_names': {
                                  'type': 'array',
                                  'items': {
                                      'type': 'string',
                                      'description': f'delivers the column name for respective table from chosen schema from Metadata: {repr(database_descriptor)}',
                                      'enum': database_descriptor.column_names_enum
                                  },
                                  'description': 'delivers the names of the columns for chosen table.'
                              }
                          },
                          'required': [
                              'schema_name', 'class_name', 'table_name', 'column_names'
                          ],
                          'additionalProperties': False
                      },
                      'strict': True
                  }
                  }
                 ]
        request = self.client.chat.completions.create(
            model='gpt-4o',
            messages=[{'role': 'user', 'content': query}],
            tools=tools,
            tool_choice='required'
        )
        tool_call = request.choices[0].message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)

        reflected_columns = database_descriptor.fetch_reflected_columns(
            database_inspection_filter=DatabaseInspectionFilter(
                schema_name=args['schema_name'],
                table_name=args['table_name']
            ),
            column_names=args['column_names']
        )

        progress_queue.put('generating the model...')
        orm_model = generate_orm_class(
            schema_name=args['schema_name'],
            class_name=args['class_name'],
            table_name=args['table_name'],
            reflected_columns=reflected_columns
        )
        return orm_model

    def _upsert_meta(self, progress_queue: Queue) -> None:
        progress_queue.put('initialising upsert orchestration service...')
        upsert_orchestration_service = self.upsert_factory_callback(
            client=self.client,
            event_orchestrator=self.event_orchestrator,
            engine=self.engine,
            ingestion_service=self.ingestion_service
        )
        progress_queue.put('upserting new vectors in meta...')
        upsert_orchestration_service.upsert_storage()

    def _retrieve_meta(self, progress_queue: Queue) -> pd.DataFrame:
        progress_queue.put('retrieving vectors from meta...')
        return self.retrieval_service.retrieve_vectors()

    def _vectorize_query(self, query: str, progress_queue: Queue) -> List[float]:
        progress_queue.put('generating query vectors...')
        vector_generator = VectorGenerator(
            client=self.client,
            datastream=query
        )
        query_vector = vector_generator.generate_vector()
        return query_vector
