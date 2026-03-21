from typing import List
from openai.types.chat import ChatCompletionToolParam

from svc_llm_inference_contracts.models import LlmOutputSpecs


def build_tool_schema(llm_output_specs: LlmOutputSpecs) -> List[ChatCompletionToolParam]:
    qualified_columns = [
        f'{schema_name}.{table_name}.{column}'
        for integration_entry in llm_output_specs.table_columns_registry.values()
        for schema_name, schema_entry in integration_entry.schemas.items()
        for table_name, columns in schema_entry.tables.items()
        for column in columns
    ]
    tool = [{
        'type': 'function',
        'function': {
            'name': 'generate_orm_class',
            'description': (
                'Function responsible for dynamically generating orm classes '
                'with schema_name, class_name, table_name and column_names '
                'which are most likely to provide the answer to user query. '
                'column_names, column_filters and column_aggregates '
                'MUST use fully qualified schema.table.column format. '
                'All selected columns must share the same schema.table prefix.'
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'integration': {
                        'type': 'string',
                        'description': f'delivers the connection id of database from Metadata: {llm_output_specs.integration_registry_repr}',
                        'enum': llm_output_specs.integrations_enum
                    },
                    'class_name': {
                        'type': 'string',
                        'description': 'delivers ORM class name for chosen table, each first letter to be capitalized.'
                    },
                    'column_names': {
                        'type': 'array',
                        'description': 'delivers the names of the columns for chosen table in schema.table.column format.',
                        'items': {
                            'type': 'string',
                            'description': f'delivers the fully qualified column name (schema.table.column) for respective table from chosen schema from Metadata: {llm_output_specs.integration_registry_repr}',
                            'enum': qualified_columns
                        }
                    },
                    'column_filters': {
                        'type': 'array',
                        'description': (
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
                                    'enum': llm_output_specs.filter_op_enum
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
                                    'description': 'delivers fully qualified column (schema.table.column) to be filtered through operator with value',
                                    'enum': qualified_columns
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
                                    'enum': llm_output_specs.agg_funcs_enum
                                },
                                'agg_column': {
                                    'type': 'string',
                                    'description': 'delivers fully qualified column (schema.table.column) to be used for aggregating the values grouped by the rest of the columns.',
                                    'enum': qualified_columns
                                }
                            },
                            'required': ['agg_func', 'agg_column'],
                            'additionalProperties': False
                        }
                    }
                },
                'required': ['integration', 'class_name', 'column_names', 'column_filters', 'column_aggregates'],
                'additionalProperties': False
            },
            'strict': True
        }
    }]
    return tool # type: ignore[return-value]
