import unittest
import uuid
import json
from unittest.mock import AsyncMock, MagicMock, patch
from svc_ai_orm_context_contracts.models import (
    ORMContextRequest,
    Context
)

from ai_orm_context_service.services.orm_context.model_providers.hugging_face.inference.inference_providers import \
    CerebrasInference


class TestCerebrasInference(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.chat_response_mock = MagicMock()
        self.provider_name = 'cerebras'
        self.provider_url = 'https://huggingface.co'

        self.request = ORMContextRequest(
            provider='Deepseek',
            model_id='Deepseek-14-build',
            query='Count the powers for strong marvel characters',
            context=Context(
                integration_registry_repr='general',
                integrations_enum=[str(uuid.uuid4()), str(uuid.uuid4())],
                schemas_enum=['marvel', 'dc', 'startrek'],
                tables_enum=['characters', 'relatives', 'realms'],
                columns_enum=['power', 'skills', 'age', 'height', 'weight', 'skills', 'name'],
                filter_op_enum=['=', '>', '<', '!='],
                agg_funcs_enum=['avg', 'sum', 'count', 'min', 'max']
            )
        )

    @patch('ai_orm_context_service.services.orm_context.model_providers.hugging_face.inference.inference_providers.cerebras.AsyncOpenAI')
    async def test_gets_model_response(
        self,
        openai_mock
    ):
        func_args = {'test-arg': 'test-value'}
        tool_call_mock = MagicMock()
        tool_call_mock.function.arguments = json.dumps(func_args)
        choices_mock = MagicMock()
        choices_mock.message.tool_calls = [tool_call_mock]
        completions_request_mock = MagicMock()
        completions_request_mock.choices = [choices_mock]
        openai_instance_mock = AsyncMock()
        openai_mock.return_value = openai_instance_mock
        openai_instance_mock.chat.completions.create.return_value = completions_request_mock

        inference = CerebrasInference(
            self.provider_name,
            self.provider_url
        )
        result = await inference.get_model_response(
            'hf-path',
            300,
            orm_context_request=self.request
        )
        openai_instance_mock.chat.completions.create.assert_awaited_once_with(
            model=f'hf-path:{self.provider_name}',
            messages=[{'role': 'user', 'content': self.request.query}],
            tools=inference._build_function_schema(self.request.context),
            tool_choice='required',
            max_tokens=300
        )
        self.assertEqual(result, func_args)
