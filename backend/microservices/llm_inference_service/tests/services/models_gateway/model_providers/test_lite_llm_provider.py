import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from llm_inference_service.services.models_gateway.exceptions import InvalidModelResponse
from llm_inference_service.services.models_gateway.model_providers.lite_llm_provider import LiteLlmProvider
from svc_llm_inference_contracts.models import ORMContextRequest, LlmOutputSpecs


class ConcreteLiteLlmProvider(LiteLlmProvider):

    def model_path(self) -> str:
        return 'openai/test-model'

    def base_kwargs(self) -> Dict[str, Any]:
        return {'model': self.model_path(), 'api_key': 'test-key'}

    def max_tokens(self) -> int:
        return 4096


def make_orm_request(**overrides) -> ORMContextRequest:
    defaults = {
        'provider': 'openai',
        'model_id': 'gpt-4o',
        'query': 'show me sales by region',
        'llm_output_specs': make_llm_output_specs(),
    }
    return ORMContextRequest(**{**defaults, **overrides})


def make_llm_output_specs(**overrides) -> LlmOutputSpecs:
    defaults = {
        'datastore_registry_repr': 'test_datastore',
        'datastores_enum': ['sales_db'],
        'schemas_enum': ['public'],
        'tables_enum': ['sales'],
        'columns_enum': ['public.sales.region', 'public.sales.amount'],
        'filter_op_enum': ['eq', 'gt', 'lt'],
        'agg_funcs_enum': ['sum', 'avg', 'count'],
        'table_columns_registry': {},
    }
    return LlmOutputSpecs(**{**defaults, **overrides})


def make_acompletion_response(content: str = 'some response\nwith two lines') -> MagicMock:
    choice = MagicMock()
    choice.message.content = content
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def make_tool_call_response(arguments: dict) -> MagicMock:
    import json
    tool_call = MagicMock()
    tool_call.function.arguments = json.dumps(arguments)
    choice = MagicMock()
    choice.message.tool_calls = [tool_call]
    resp = MagicMock()
    resp.choices = [choice]
    return resp


class TestResolveMaxTokens(unittest.TestCase):

    def setUp(self):
        self.provider = ConcreteLiteLlmProvider(completion_fn=AsyncMock())

    def test_returns_ceiling_when_no_request(self):
        self.assertEqual(self.provider._resolve_max_tokens(None), 4096)

    def test_returns_requested_when_below_ceiling(self):
        self.assertEqual(self.provider._resolve_max_tokens(1024), 1024)

    def test_clamps_to_ceiling_when_above(self):
        self.assertEqual(self.provider._resolve_max_tokens(9999), 4096)

    def test_returns_ceiling_when_requested_equals_ceiling(self):
        self.assertEqual(self.provider._resolve_max_tokens(4096), 4096)

    def test_returns_one_when_requested_is_one(self):
        self.assertEqual(self.provider._resolve_max_tokens(1), 1)


class TestProviderLabel(unittest.TestCase):

    def test_returns_class_name(self):
        provider = ConcreteLiteLlmProvider(completion_fn=AsyncMock())
        self.assertEqual(provider._provider_label(), 'ConcreteLiteLlmProvider')


class TestPromptModel(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_completion = AsyncMock(return_value=make_acompletion_response())
        self.provider = ConcreteLiteLlmProvider(completion_fn=self.mock_completion)

    async def test_returns_response_content(self):
        self.mock_completion.return_value = make_acompletion_response('hello world')
        result = await self.provider.prompt_model('hi')
        self.assertEqual(result, 'hello world')

    async def test_passes_prompt_as_user_message(self):
        await self.provider.prompt_model('my prompt')
        call_kwargs = self.mock_completion.call_args.kwargs
        self.assertEqual(
            call_kwargs['messages'],
            [{'role': 'user', 'content': 'my prompt'}]
        )

    async def test_resolves_max_tokens(self):
        await self.provider.prompt_model('hi', max_tokens=512)
        self.assertEqual(self.mock_completion.call_args.kwargs['max_tokens'], 512)

    async def test_clamps_max_tokens_to_ceiling(self):
        await self.provider.prompt_model('hi', max_tokens=99999)
        self.assertEqual(self.mock_completion.call_args.kwargs['max_tokens'], 4096)

    async def test_uses_base_kwargs(self):
        await self.provider.prompt_model('hi')
        call_kwargs = self.mock_completion.call_args.kwargs
        self.assertEqual(call_kwargs['model'], 'openai/test-model')
        self.assertEqual(call_kwargs['api_key'], 'test-key')


class TestExecuteQuery(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_completion = AsyncMock(return_value=make_acompletion_response())
        self.provider = ConcreteLiteLlmProvider(completion_fn=self.mock_completion)

    async def test_returns_valid_multiline_response(self):
        self.mock_completion.return_value = make_acompletion_response('line one\nline two')
        result = await self.provider.execute_query('some query')
        self.assertEqual(result, 'line one\nline two')

    async def test_raises_on_single_line_response(self):
        self.mock_completion.return_value = make_acompletion_response('just one line')
        with self.assertRaises(InvalidModelResponse):
            await self.provider.execute_query('some query')

    async def test_raises_on_empty_response(self):
        self.mock_completion.return_value = make_acompletion_response('')
        with self.assertRaises(InvalidModelResponse):
            await self.provider.execute_query('some query')

    async def test_error_message_contains_model_and_provider(self):
        self.mock_completion.return_value = make_acompletion_response('single line')
        with self.assertRaises(InvalidModelResponse) as ctx:
            await self.provider.execute_query('some query')
        self.assertIn('openai/test-model', str(ctx.exception))
        self.assertIn('ConcreteLiteLlmProvider', str(ctx.exception))


class TestExecuteStructuredQuery(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.raw_args = {
            'data_store': 'sales_db',
            'class_name': 'SalesRecord',
            'column_names': ['public.sales.region', 'public.sales.amount'],
            'column_filters': [],
            'column_aggregates': [],
        }
        self.mock_completion = AsyncMock(return_value=make_tool_call_response(self.raw_args))
        self.provider = ConcreteLiteLlmProvider(completion_fn=self.mock_completion)

    async def test_returns_parsed_response(self):
        parsed = {'data_store': 'sales_db', 'class_name': 'SalesRecord'}
        with patch(
            'llm_inference_service.services.models_gateway.model_providers.lite_llm_provider.parse_response_schema',
            return_value=parsed
        ), patch(
            'llm_inference_service.services.models_gateway.model_providers.lite_llm_provider.build_tool_schema',
            return_value=[]
        ):
            result = await self.provider.execute_structured_query(make_orm_request())
            self.assertEqual(result, parsed)

    async def test_passes_query_as_user_message(self):
        with patch(
            'llm_inference_service.services.models_gateway.model_providers.lite_llm_provider.parse_response_schema',
            return_value={}
        ), patch(
            'llm_inference_service.services.models_gateway.model_providers.lite_llm_provider.build_tool_schema',
            return_value=[]
        ):
            await self.provider.execute_structured_query(make_orm_request(query='show me revenue'))
            messages = self.mock_completion.call_args.kwargs['messages']
            self.assertEqual(messages, [{'role': 'user', 'content': 'show me revenue'}])

    async def test_passes_tool_choice_required(self):
        with patch(
            'llm_inference_service.services.models_gateway.model_providers.lite_llm_provider.parse_response_schema',
            return_value={}
        ), patch(
            'llm_inference_service.services.models_gateway.model_providers.lite_llm_provider.build_tool_schema',
            return_value=[]
        ):
            await self.provider.execute_structured_query(make_orm_request())
            self.assertEqual(self.mock_completion.call_args.kwargs['tool_choice'], 'required')

    async def test_respects_requested_max_tokens(self):
        with patch(
            'llm_inference_service.services.models_gateway.model_providers.lite_llm_provider.parse_response_schema',
            return_value={}
        ), patch(
            'llm_inference_service.services.models_gateway.model_providers.lite_llm_provider.build_tool_schema',
            return_value=[]
        ):
            await self.provider.execute_structured_query(make_orm_request())
            self.assertEqual(self.mock_completion.call_args.kwargs['max_tokens'], 4096)
