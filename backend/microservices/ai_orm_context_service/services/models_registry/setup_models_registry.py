from .models_registry import ModelsRegistry


def setup_models_registry() -> ModelsRegistry:
    models_registry = ModelsRegistry()
    return models_registry
