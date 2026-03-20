from llm_inference_service.services.models_gateway.exceptions import InferenceProviderMissing
from llm_inference_service.services.models_gateway.model_providers.hugging_face.inference.inference_providers.base import InferenceProviderBase
from .registry import INFERENCE_REGISTRY


def dispatch_inference_provider(inference: str, url: str) -> InferenceProviderBase:
    if inference not in INFERENCE_REGISTRY:
        raise InferenceProviderMissing(f'Inference provider not found: {inference}')
    inference_cls = INFERENCE_REGISTRY.get(inference)
    inference = inference_cls(inference, url)
    return inference
