import yaml
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any


logger = logging.getLogger(__name__)


class ModelsRegistry:
    def __init__(self, config_path: Optional[Path] = None):
        self._config_path = config_path or Path(__file__).resolve().parents[2] / 'config/models_registry.yaml'
        self._registry: Dict[str, Dict[str, Any]] = {}
        self._load_registry()

    def _load_registry(self) -> None:
        if not self._config_path.exists():
            msg = f'Provider registry file not found: {self._config_path}'
            logger.error(msg)
            raise FileNotFoundError(msg)

        with open(self._config_path, 'r') as file:
            try:
                raw = yaml.safe_load(file)
            except yaml.YAMLError as e:
                logger.error(f'Failed to parse YAML: {e}')
                raise

        providers = raw.get('providers')
        if not isinstance(providers, dict):
            msg = 'Invalid provider registry format: missing or malformed providers key.'
            logger.error(msg)
            raise ValueError(msg)

        self._registry = providers
        logger.info(f'Loaded {len(self._registry)} providers from registry.')

    def reload(self) -> None:
        logger.info('Reloading model registry from config...')
        self._load_registry()

    def list_models(self) -> List[Dict[str, str | List[str]]]:
        return [
            {'provider': provider, 'model_id': model_id, 'label': meta.get('label', model_id), 'tags': meta.get('tags')}
            for provider, model in self._registry.items()
            for model_id, meta in model.items()
        ]

    def get_model(self, provider: str, model_id: str) -> Dict[str, Any]:
        model_registry = self.get_model_registry(provider)
        model = model_registry.get(model_id)
        if not model:
            msg = f'Model: {model_id} not found in registry.'
            logger.warning(msg)
            raise ValueError(msg)
        return model
    
    def get_model_registry(self, provider: str) -> Dict[str, Any]:
        model_registry = self._registry.get(provider)
        if not model_registry:
            msg = f'Provider: {provider} not found in registry.'
            logger.warning(msg)
            raise ValueError(msg)
        return model_registry

    def all(self) -> Dict[str, Dict[str, Any]]:
        return self._registry.copy()

    def get_by_tag(self, tag: str) -> Dict[str, Dict[str, Any]]:
        return {
            model_id: meta
            for _, model in self._registry.items()
            for model_id, meta in model.items()
            if tag in meta.get('tags', [])
        }
