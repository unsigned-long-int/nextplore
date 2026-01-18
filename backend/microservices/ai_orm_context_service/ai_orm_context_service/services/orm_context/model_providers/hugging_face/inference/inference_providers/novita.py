import json
import os
from openai import AsyncOpenAI
from typing import Dict, Any, List
from svc_ai_orm_context_contracts.models import ORMContextRequest

from .base import InferenceProviderBase


class NovitaInference(InferenceProviderBase):
    def __init__(self, provider_name: str, provider_url: str) -> None:
        self.provider_name = provider_name
        self.client = AsyncOpenAI(
            base_url=provider_url,
            api_key=os.getenv('HUGGINGFACE_API_KEY')
        )
    
    async def get_model_response(self, hf_path: str, max_tokens: int, orm_context_request: ORMContextRequest) -> Dict[str, Any]:
        context = orm_context_request.context
        tools = self._build_function_schema(context)
        request = await self.client.chat.completions.create(
            model=f'{hf_path}:{self.provider_name}',
            messages=[{'role': 'user', 'content': orm_context_request.query}],
            tools=tools,
            tool_choice='required',
            max_tokens=max_tokens
        )
        tool_call = request.choices[0].message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        return args 

    def _build_function_schema(self, context) -> List[Dict[str, Any]]:
        tools = [{'type': 'function',
                  'function': {
                      'name': 'generate_orm_class',
                      'description': (
                          'Function:  responsible for dynamically generating orm classes'
                          'with schema_name, class_name, table_name and column_names'
                          'which are most likely to provide the answer to user query.'),
                      'parameters': {
                          'type': 'object',
                          'properties': {
                              'integration': {
                                  'type': 'string',
                                  'description': f'delivers the connection id of database from Metadata: {context.integration_registry_repr}',
                                  'enum': context.integrations_enum
                              },
                              'schema_name': {
                                  'type': 'string',
                                  'description': f'delivers the name of the schema from Metadata: {context.integration_registry_repr}',
                                  'enum': context.schemas_enum
                              },
                              'class_name': {
                                  'type': 'string',
                                  'description': 'delivers ORM class name for chosen table, each first letter to be capitalized.'
                              },
                              'table_name': {
                                  'type': 'string',
                                  'description': f'delivers the name of table for respective schema from Metadata: {context.integration_registry_repr}',
                                  'enum': context.tables_enum
                              },
                              'column_names': {
                                  'type': 'array',
                                  'items': {
                                      'type': 'string',
                                      'description': f'delivers the column name for respective table from chosen schema from Metadata: {context.integration_registry_repr}',
                                      'enum': context.columns_enum
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
                                                'enum': context.filter_op_enum
                                            },
                                            'value': {
                                                'type': ['number', 'string'],
                                                'description': 'delivers value to be used by operator'
                                            },
                                            'filter_column': {
                                                'type': 'string',
                                                'description': 'delivers columns to be filtered through operator with value',
                                                'enum': context.columns_enum
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
                                                'enum': context.agg_funcs_enum
                                            },
                                            'agg_column': {
                                                'type': 'string',
                                                'description': 'Delivers columns to be used for aggregating the values grouped by the rest of the columns.',
                                                'enum': context.columns_enum
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
        return tools
