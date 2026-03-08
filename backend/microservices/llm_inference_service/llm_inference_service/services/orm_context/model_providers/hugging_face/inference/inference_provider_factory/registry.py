from typing import Dict, Type

from llm_inference_service.services.orm_context.model_providers.hugging_face.inference.inference_providers import (
    CerebrasInference,
    NovitaInference,
    InferenceProviderBase
)

INFERENCE_REGISTRY: Dict[str, Type[InferenceProviderBase]] = {
    'cerebras': CerebrasInference,
    'novita': NovitaInference
}
