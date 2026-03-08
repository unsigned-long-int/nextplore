from fastapi import Request
from nextplore_orchestrator.clients.llm_inference import LlmInferenceClient


def get_llm_inference_client(request: Request) -> LlmInferenceClient:
    return request.app.state.clients.llm_inference_client
