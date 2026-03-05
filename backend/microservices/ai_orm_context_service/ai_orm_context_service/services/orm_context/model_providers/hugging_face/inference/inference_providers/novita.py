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
                                  'description': ('List of filters for the SQL WHERE clause. Important rules: '
                                                '1. When the user references multiple entities by name (e.g. "Gimli and Frodo", "both X and Y"), use a SINGLE filter with operator "in" and an array of values - never multiple "like" filters. '
                                                '2. When the user provides a partial name for a SINGLE entity, use "like" with wildcards e.g. "%Frodo%". '
                                                '3. When the user provides a partial name among multiple entities, use "in" with the partial name expanded using % wildcards as separate entries. '
                                                '4. Multiple filters are combined with AND - never use AND logic to match different values of the same column.'),
                                  'items': {
                                       'type': 'object',
                                       'description': 'delivers the filter values for sql statement if needed to filter selected column.',
                                       'properties': {
                                            'operator': {
                                                'type': 'string',
                                                'description': ( 'Operator for filtering. Rules: '
                                                                '"in" — use when filtering by multiple specific values (e.g. "Gimli and Frodo", "these three countries"). '
                                                                '"like" — use ONLY for a single partial/fuzzy match (e.g. "someone named Fro%"). '
                                                                'Never apply multiple "like" filters with AND when the user lists multiple entities - use "in" instead. '
                                                                '"==" — exact single value match. '
                                                                '">", "<", ">=", "<=" - numeric or date comparisons.'),
                                                'enum': context.filter_op_enum
                                            },
                                            'value': {
                                                'type': ['number', 'string', 'array'],
                                                'description': (
                                                    'Value to be used by operator. '
                                                    'For "in" operator, provide an array of values e.g. ["Gimli", "Frodo Baggins"]. '
                                                    'For "like" operator, provide a single string with % wildcards e.g. "%Frodo%". '
                                                    'Never use "like" multiple times for multiple entities - use "in" instead.'
                                                ),
                                                'items': {'type': ['string', 'number']}
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
