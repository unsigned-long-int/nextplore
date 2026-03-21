import json
import os
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionUserMessageParam, ChatCompletionToolParam
from typing import Dict, Any, List
from llm_inference_service.services.rag_pipeline.ai_adapter import build_tool_schema
from svc_llm_inference_contracts.models import ORMContextRequest

from .base import InferenceProviderBase


class NovitaInference(InferenceProviderBase):
    def __init__(self, provider_name: str, provider_url: str) -> None:
        super().__init__(provider_name, provider_url)
        self.client = AsyncOpenAI(
            base_url=provider_url,
            api_key=os.getenv('HUGGINGFACE_API_KEY')
        )
    
    async def get_structured_model_response(self, hf_path: str, max_tokens: int, orm_context_request: ORMContextRequest) -> Dict[str, Any]:
        llm_output_specs = orm_context_request.llm_output_specs
        tools: List[ChatCompletionToolParam] = build_tool_schema(llm_output_specs)
        messages: List[ChatCompletionUserMessageParam] = [{'role': 'user', 'content': orm_context_request.query}]
        request = await self.client.chat.completions.create(
            model=f'{hf_path}:{self.provider_name}',
            messages=messages,
            tools=tools,
            tool_choice='required',
            max_tokens=max_tokens
        )
        tool_call = request.choices[0].message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        return args

    async def get_model_response(
        self,
        hf_path: str,
        max_tokens: int,
        query: str
    ) -> str:
        messages: List[ChatCompletionUserMessageParam] = [{'role': 'user', 'content': query}]
        response = await self.client.chat.completions.create(
            model=f'{hf_path}:{self.provider_name}',
            messages=messages,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
