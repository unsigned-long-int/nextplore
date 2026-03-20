import os
import json
from typing import Dict, List, Any
from pydantic import ValidationError
from openai.types.chat import ChatCompletionUserMessageParam, ChatCompletionToolParam
from svc_llm_inference_contracts.models import ORMContextResponse, ORMContextRequest, LlmOutputSpecs
from nextplore_sdk.open_ai_client_loader.open_ai_client_loader import load_open_ai_client

from llm_inference_service.services.models_gateway.model_providers.base import BaseProvider
from llm_inference_service.services.models_gateway.exceptions import InvalidModelResponse


class OpenAIProvider(BaseProvider):
    def __init__(self, model_id: str) -> None:
        self.model_id = model_id
        self.client = load_open_ai_client(os.getenv('OPENAI_API_KEY'))

    async def execute_structured_query(self, orm_context_request: ORMContextRequest) -> Dict[str, Any]:
        llm_output_specs = orm_context_request.llm_output_specs
        tools: List[ChatCompletionToolParam] = self._build_function_schema(llm_output_specs)
        messages: List[ChatCompletionUserMessageParam] = [
            {'role': 'user', 'content': orm_context_request.query}
        ]

        request = await self.client.chat.completions.create(
            model=self.model_id,
            messages=messages,
            tools=tools,
            tool_choice='required'
        )
        tool_call = request.choices[0].message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)

        if not self._validate_response_schema(args):
            msg = f'Invalid model response. Model: {self.model_id}. Provider: OpenAI'
            raise InvalidModelResponse(msg)
        return args

    async def execute_query(self, query: str) -> str:
        response = await self.client.responses.create(
            model=self.model_id,
            input=query,
        )
        if len(response.output_text.strip().splitlines()) < 2:
            raise InvalidModelResponse(f'Invalid model response. Model: {self.model_id}. Provider: OpenAI')
        return response.output_text
    
    def _validate_response_schema(self, model_response: Dict[str, Any]) -> bool:
        try:
            ORMContextResponse(**model_response)
            return True
        except ValidationError:
            return False
    
    def _build_function_schema(self, context: LlmOutputSpecs) -> List[ChatCompletionToolParam]:
        tools = [{'type': 'function',
                  'function': {
                      'name': 'generate_orm_class',
                      'description': (
                          'Function: responsible for dynamically generating orm classes '
                          'with schema_name, class_name, table_name and column_names '
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
                                  'description':  (
                                        'List of filters for the SQL WHERE clause. Important rules: '
                                        '1. When the user references multiple entities by name (e.g. "Gimli and Frodo", "both X and Y"), use a SINGLE filter with operator "in" and an array of values - never multiple "like" filters. '
                                        '2. When the user provides a partial name for a SINGLE entity, use "like" with wildcards e.g. "%Frodo%". '
                                        '3. When the user provides a partial name among multiple entities, use "in" with the partial name expanded using % wildcards as separate entries. '
                                        '4. Multiple filters are combined with AND - never use AND logic to match different values of the same column.'
                                    ),
                                  'items': {
                                       'type': 'object',
                                       'description': 'delivers the filter values for sql statement if needed to filter selected column.',
                                       'properties': {
                                            'operator': {
                                                'type': 'string',
                                                'description': (
                                                    'Operator for filtering. Rules: '
                                                    '"in" - use when filtering by multiple specific values (e.g. "Gimli and Frodo", "these three countries"). '
                                                    '"like" - use ONLY for a single partial/fuzzy match (e.g. "someone named Fro%"). '
                                                    'Never apply multiple "like" filters with AND when the user lists multiple entities - use "in" instead. '
                                                    '"==" - exact single value match. '
                                                    '">", "<", ">=", "<=" - numeric or date comparisons.'
                                                ),
                                                'enum': context.filter_op_enum
                                            },
                                            'value': {
                                                'type': ['number', 'string'],
                                                'description': (
                                                    'Value to be used by operator. '
                                                    'For "in" operator, provide a comma-separated string e.g. "Gimli, Frodo Baggins". '
                                                    'For "like" operator, provide a single string with % wildcards e.g. "%Frodo%". '
                                                ),
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
        return tools # type: ignore[return-value]