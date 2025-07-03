import json
import pandas as pd

from dataclasses import dataclass
from typing import List
from uuid import UUID
from openai import OpenAI
from sqlalchemy.engine import Row


from core.context_retriever import retrieve_contextual_vector_matrix
from core.vector_generation_service import VectorGenerator
from core.database.inspection import inspect_integration_registry
from core.database.filter.factory import create_contextual_filters
from core.database.filter.specs import IntegrationIdSpec, SchemaNameSpec, TableNameSpec
from core.database.filter.propagation import filter_integrations
from .orm_request import ORMRequest
from .orm_meta import generate_orm_class


@dataclass 
class AIORMFactory:
    client: OpenAI
    vectors_meta: List[Row]

    def retrieve_orm_request(self, query: str) -> ORMRequest:
        query_vector = self._vectorize_query(query)
        orm_vectors = pd.DataFrame([dict(row._mapping) for row in self.vectors_meta])
        contextual_vector_matrix = retrieve_contextual_vector_matrix(
            query_vector=query_vector,
            orm_vectors=orm_vectors
        )

        integration_spec, schema_spec, table_spec = create_contextual_filters(
            contextual_vector_matrix
        )

        integration_registry = inspect_integration_registry(
            integration_ids=contextual_vector_matrix['integration_id'],
            integration_spec=integration_spec,
            schema_spec=schema_spec,
            table_spec=table_spec
        )

        tools = [{'type': 'function',
                  'function': {
                      'name': 'generate_orm_class',
                      'description': f'Function: {generate_orm_class.__doc__}.',
                      'parameters': {
                          'type': 'object',
                          'properties': {
                              'integration': {
                                  'type': 'string',
                                  'description': f'delivers the connection id of database from Metadata: {repr(integration_registry)}',
                                  'enum': integration_registry.integrations_enum
                              },
                              'schema_name': {
                                  'type': 'string',
                                  'description': f'delivers the name of the schema from Metadata: {repr(integration_registry)}',
                                  'enum': integration_registry.schemas_enum
                              },
                              'class_name': {
                                  'type': 'string',
                                  'description': f'delivers ORM class name for chosen table, each first letter to be capitalized.'
                              },
                              'table_name': {
                                  'type': 'string',
                                  'description': f'delivers the name of table for respective schema from Metadata: {repr(integration_registry)}',
                                  'enum': integration_registry.tables_enum
                              },
                              'column_names': {
                                  'type': 'array',
                                  'items': {
                                      'type': 'string',
                                      'description': f'delivers the column name for respective table from chosen schema from Metadata: {repr(integration_registry)}',
                                      'enum': integration_registry.columns_enum
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
                                                'enum': integration_registry.filter_op_enum
                                            },
                                            'value': {
                                                'type': ['number', 'string'],
                                                'description': 'delivers value to be used by operator'
                                            },
                                            'filter_column': {
                                                'type': 'string',
                                                'description': 'delivers columns to be filtered through operator with value',
                                                'enum': integration_registry.columns_enum
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
                                                'enum': integration_registry.agg_funcs_enum
                                            },
                                            'agg_column': {
                                                'type': 'string',
                                                'description': 'Delivers columns to be used for aggregating the values grouped by the rest of the columns.',
                                                'enum': integration_registry.columns_enum
                                            }
                                        },
                                        'required': ['agg_func', 'agg_column'],
                                        'additionalProperties': False
                                    }
                                }
                            },
                            'required': [
                                'integration','schema_name', 'class_name', 'table_name', 'column_names', 'column_filters', 'column_aggregates'
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
        integration_spec = IntegrationIdSpec({UUID(args['integration'])})
        schema_spec = SchemaNameSpec({UUID(args['integration']): {args['schema_name']}})
        table_spec = TableNameSpec({UUID(args['integration']):args['table_name']})

        filtered_integration_registry = filter_integrations(
            integrations=integration_registry.integrations,
            integration_spec=integration_spec,
            schema_spec=schema_spec,
            table_spec=table_spec
        )
        orm_model = generate_orm_class(
            **filtered_integration_registry.fetch_first_matched_metadata(),
            class_name=args['class_name']
        )

        return ORMRequest(
            orm_model=orm_model,
            selected_columns=args['column_names'],
            aggregates=args['column_aggregates'],
            filters=args['column_filters']
        )

    def _vectorize_query(self, query: str) -> List[float]:
        vector_generator = VectorGenerator(
            client=self.client,
            datastream=query
        )
        query_vector = vector_generator.generate_vector()
        return query_vector
    