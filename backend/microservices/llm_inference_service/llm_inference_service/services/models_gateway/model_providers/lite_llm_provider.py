import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from llm_inference_service.services.rag_pipeline.ai_adapter import build_tool_schema, parse_response_schema
from llm_inference_service.services.models_gateway.exceptions import InvalidModelResponse

from svc_llm_inference_contracts.models import ORMContextRequest


class LiteLlmProvider(ABC):
    def __init__(self, completion_fn=None):
        if completion_fn is None:
            from litellm import acompletion
            completion_fn = acompletion
        self._acompletion = completion_fn

    @abstractmethod
    def model_path(self) -> str:
        ...


    @abstractmethod
    def base_kwargs(self) -> Dict[str, Any]:
        ...

    @abstractmethod
    def max_tokens(self) -> int:
        ...

    def _resolve_max_tokens(self, requested: Optional[int] = None) -> int:
        ceiling = self.max_tokens()
        if requested is None:
            return ceiling

        return min(ceiling, requested)

    def _provider_label(self) -> str:
        return self.__class__.__name__

    async def execute_structured_query(
            self,
            orm_context_request: ORMContextRequest,
    ) -> Dict[str, Any]:
        tools = build_tool_schema(orm_context_request.llm_output_specs)
        messages = [{'role': 'user', 'content': orm_context_request.query}]

        resp = await self._acompletion(
            **self.base_kwargs(),
            messages=messages,
            tools=tools,
            tool_choice='required',
            max_tokens=self._resolve_max_tokens(getattr(orm_context_request, 'max_tokens', None)),
        )

        tool_call = resp.choices[0].message.tool_calls[0]
        raw = json.loads(tool_call.function.arguments)

        return parse_response_schema(
            raw,
            model_id=self.model_path(),
            provider_name=self._provider_label(),
        )

    async def execute_query(self, query: str) -> str:
        response = await self.prompt_model(query)
        if len(response.strip().splitlines()) < 2:
            raise InvalidModelResponse(
                f'Invalid chat response. Model: {self.model_path()}. '
                f'Provider: {self._provider_label()}'
            )
        return response

    async def prompt_model(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        resp = await self._acompletion(
            **self.base_kwargs(),
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=self._resolve_max_tokens(max_tokens)
        )
        return resp.choices[0].message.content