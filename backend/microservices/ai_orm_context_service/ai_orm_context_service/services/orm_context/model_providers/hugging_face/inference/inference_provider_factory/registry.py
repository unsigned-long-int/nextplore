from typing import Dict, Type

from ai_orm_context_service.services.orm_context.model_providers.hugging_face.inference.inference_providers import (
    CerebrasInference,
    NovitaInference,
    InferenceProviderBase
)

INFERENCE_REGISTRY: Dict[str, Type[InferenceProviderBase]] = {
    'cerebras': CerebrasInference,
    'novita': NovitaInference
}
