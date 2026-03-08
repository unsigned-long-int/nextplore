from fastapi import Request

from .models_registry import ModelsRegistry


def get_models_registry(request: Request) -> ModelsRegistry:
    return request.app.state.models_registry
