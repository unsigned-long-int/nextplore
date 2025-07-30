import json

from dataclasses import dataclass
from typing import List
from openai import OpenAI

from shared.contracts.integration_service import IntegrationMetadataRequest
from shared.contracts.vector_service import QDrantVectorRequest
from shared.contracts.vector_service import VectorMetaRequest
from shared.database.connection_builder import build_connection_string, ConnectionMeta
from shared.identity_service.user_identity import UserIdentity
from shared.contracts.integration_service import FilteredCrawlRequest
from internal_services.context import retrieve_context_meta
from clients import EmbeddingClient, IntegrationClient, VectorClient
from .orm_factory import ORMFactory
from .orm_request import ORMRequest


@dataclass 
class AIORMRequestFactory:
    client: OpenAI
    user_identity: UserIdentity
    vector_client: VectorClient
    integration_client: IntegrationClient
    embedding_client: EmbeddingClient


    async def retrieve_orm_request(self, query: str) -> ORMRequest:
        embedding = await self._get_query_embedding(query)
        payload = QDrantVectorRequest(
            embedding=embedding
        )
        response = await self.vector_client.get_qdrant_vectors(payload)

        payload = VectorMetaRequest(
            vector_ids=response.vector_ids
        )
        vectors_meta = await self.vector_client.get_vector_metas(payload)
        integrations, schemas, tables = retrieve_context_meta(vectors_meta)

        payload = FilteredCrawlRequest(
            integrations=integrations,
            schemas=schemas,
            tables=tables
        )
        integration_registry = await self.integration_client.crawl_filtered_integration(payload)

        tools = [{'type': 'function',
                  'function': {
                      'name': 'generate_orm_class',
                      'description': f'Function: {ORMFactory.__doc__}.',
                      'parameters': {
                          'type': 'object',
                          'properties': {
                              'integration': {
                                  'type': 'string',
                                  'description': f'delivers the connection id of database from Metadata: {integration_registry.integration_registry_repr}',
                                  'enum': integration_registry.integrations_enum
                              },
                              'schema_name': {
                                  'type': 'string',
                                  'description': f'delivers the name of the schema from Metadata: {integration_registry.integration_registry_repr}',
                                  'enum': integration_registry.schemas_enum
                              },
                              'class_name': {
                                  'type': 'string',
                                  'description': f'delivers ORM class name for chosen table, each first letter to be capitalized.'
                              },
                              'table_name': {
                                  'type': 'string',
                                  'description': f'delivers the name of table for respective schema from Metadata: {integration_registry.integration_registry_repr}',
                                  'enum': integration_registry.tables_enum
                              },
                              'column_names': {
                                  'type': 'array',
                                  'items': {
                                      'type': 'string',
                                      'description': f'delivers the column name for respective table from chosen schema from Metadata: {integration_registry.integration_registry_repr}',
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
        print(tools)
        request = self.client.chat.completions.create(
            model='gpt-4o',
            messages=[{'role': 'user', 'content': query}],
            tools=tools,
            tool_choice='required'
        )
        tool_call = request.choices[0].message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)

        integration_metadata_request = IntegrationMetadataRequest(
            integration_id=args['integration'],
            user_id=self.user_identity.user_id,
            organization_id=self.user_identity.organization_id
        )
        integration = await self.integration_client.get_integration(integration_metadata_request)
        connection_meta = ConnectionMeta(
            service_type=integration.service_type,
            auth_method=integration.auth_method,
            host=integration.host,
            port=integration.port,
            database_name=integration.database_name,
            username=integration.username,
            password=integration.password,
            kerberos_principal=integration.kerberos_principal,
            windows_domain=integration.windows_domain,
            extra_options=integration.extra_options
        )
        connection_string = build_connection_string(connection_meta)

        orm_factory = ORMFactory(
            integration_id=args['integration'],
            schema_name=args['schema_name'],
            class_name=args['class_name'],
            table_name=args['table_name'],
            connection_string=connection_string
        )

        orm_model = orm_factory.generate_orm_class()

        return ORMRequest(
            orm_model=orm_model,
            integration_id=args['integration'],
            selected_columns=args['column_names'],
            aggregates=args['column_aggregates'],
            filters=args['column_filters']
        )
    
    async def _get_query_embedding(self, query: str) -> List[float]:
        query_vector_response = await self.embedding_client.embed(query)
        query_vector = query_vector_response.embedding
        return query_vector