import json
import pandas as pd
from typing import Callable

from sqlalchemy import Engine
from dataclasses import dataclass
from openai import OpenAI
from typing import List, Optional, Callable, Dict

from core.database.user_database_inspector import DatabaseInspectionFilter
from core.database.database_metadata_ingestor import IngestionServiceProtocol
from core.database.database_metadata_retriever import RetrievalServiceProtocol
from core.database.user_database_inspector import fetch_database_descriptor
from core.vector_generation_service import VectorGenerator
from services.event_orchestration_service.event_orchestrator import EventOrchestrator
from core.context_retriever import retrieve_contextual_vector_matrix
from .orm_meta import generate_orm_class


@dataclass
class ORMRequest:
    orm_model: type
    selected_columns: List[str]
    aggregates: List[Dict[str, str]]
    filters: List[Dict[str, str | int]]


@dataclass
class AIORMFactory:
    client: OpenAI
    event_orchestrator: EventOrchestrator
    engine: Engine
    ingestion_service: IngestionServiceProtocol
    retrieval_service: RetrievalServiceProtocol
    upsert_factory_callback: Optional[Callable] = None

    def retrieve_orm_request(self, query: str) -> ORMRequest:
        if self.upsert_factory_callback:
            self._upsert_meta()

        orm_vectors = self._retrieve_meta()
        query_vector = self._vectorize_query(query)

        contextual_vector_matrix = retrieve_contextual_vector_matrix(
            query_vector=query_vector,
            orm_vectors=orm_vectors
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
                              },
                              'column_filters': {
                                  'type': 'array',
                                  'description': 'the list of filters as dict containing operator, value and column for filtering. Can be empty if not necessary.',
                                  'items': {
                                       'type': 'object',
                                       'description': 'delivers the filter values for sql statement if needed to filter selected column.',
                                       'properties': {
                                            'operator': {
                                                'type': 'string',
                                                'description': 'delivers operator to be used for filtering',
                                                'enum': database_descriptor.filter_op_enum
                                            },
                                            'value': {
                                                'type': ['number', 'string'],
                                                'description': 'delivers value to be used by operator'
                                            },
                                            'filter_column': {
                                                'type': 'string',
                                                'description': 'delivers columns to be filtered through operator with value',
                                                'enum': database_descriptor.column_names_enum
                                            }
                                        },
                                        'required': ['operator', 'value', 'filter_column'],
                                        'additionalProperties': False
                                    }
                                },
                                'column_aggregates': {
                                    'type': 'array',
                                    'description': 'the list of columns and aggregate commands used (avg, sum, min, max). Can be empty if not necessary.',
                                    'items': {
                                        'type': 'object',
                                        'description': 'delivers the aggregates for sql statement if needed to aggregate selected columns.',
                                        'properties': {
                                            'agg_func': {
                                                'type': 'string',
                                                'description': 'aggregate function to be used on column.',
                                                'enum': database_descriptor.agg_funcs_enum
                                            },
                                            'agg_column': {
                                                'type': 'string',
                                                'description': 'Delivers columns to be used for aggregating the values grouped by the rest of the columns.',
                                                'enum': database_descriptor.column_names_enum
                                            }
                                        },
                                        'required': ['agg_func', 'agg_column'],
                                        'additionalProperties': False
                                    }
                                }
                            },
                            'required': [
                                'schema_name', 'class_name', 'table_name', 'column_names', 'column_filters', 'column_aggregates'
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
        print(tools)
        tool_call = request.choices[0].message.tool_calls[0]
        print(tool_call)
        args = json.loads(tool_call.function.arguments)

        reflected_columns = database_descriptor.fetch_reflected_columns(
            DatabaseInspectionFilter(
                schema_name=args['schema_name'],
                table_name=args['table_name']
            )
        )
        orm_model = generate_orm_class(
            schema_name=args['schema_name'],
            class_name=args['class_name'],
            table_name=args['table_name'],
            reflected_columns=reflected_columns
        )
        return ORMRequest(
            orm_model=orm_model, 
            selected_columns=args['column_names'], 
            aggregates=args['column_aggregates'],
            filters=args['column_filters']
            )

    def _upsert_meta(self) -> None:
        upsert_orchestration_service = self.upsert_factory_callback(
            client=self.client,
            event_orchestrator=self.event_orchestrator,
            engine=self.engine,
            ingestion_service=self.ingestion_service
        )
        upsert_orchestration_service.upsert_storage()

    def _retrieve_meta(self) -> pd.DataFrame:
        return self.retrieval_service.retrieve_vectors()

    def _vectorize_query(self, query: str) -> List[float]:
        vector_generator = VectorGenerator(
            client=self.client,
            datastream=query
        )
        query_vector = vector_generator.generate_vector()
        return query_vector
