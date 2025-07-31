from pathlib import Path
from typing import Optional, Dict, List, Any
import yaml
import logging

logger = logging.getLogger(__name__)


class ModelRegistry:
    _instance = None

    def __new__(cls, config_path: Optional[Path] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: Optional[Path] = None):
        if self._initialized:
            return

        self._config_path = config_path or Path(__file__).resolve().parents[2] / 'config/model_registry.yaml'
        self._registry: Dict[str, Dict[str, Any]] = {}

        self._load_registry()
        self._initialized = True

    def _load_registry(self) -> None:
        if not self._config_path.exists():
            msg = f'Model registry file not found: {self._config_path}'
            logger.error(msg)
            raise FileNotFoundError(msg)

        with open(self._config_path, 'r') as file:
            try:
                raw = yaml.safe_load(file)
            except yaml.YAMLError as e:
                logger.error(f'Failed to parse YAML: {e}')
                raise

        models = raw.get('models')
        if not isinstance(models, dict):
            msg = 'Invalid model registry format: missing or malformed models key.'
            logger.error(msg)
            raise ValueError(msg)

        self._registry = models
        logger.info(f'Loaded {len(self._registry)} models from registry.')

    def reload(self) -> None:
        logger.info('Reloading model registry from config...')
        self._load_registry()

    def list_models(self) -> List[Dict[str, str]]:
        return [
            {'value': model_id, 'label': meta.get('label', model_id)}
            for model_id, meta in self._registry.items()
        ]

    def get_model(self, model_id: str) -> Dict[str, Any]:
        model = self._registry.get(model_id)
        if not model:
            msg = f'Model: {model_id} not found in registry.'
            logger.warning(msg)
            raise ValueError(msg)
        return model

    def all(self) -> Dict[str, Dict[str, Any]]:
        return self._registry.copy()

    def get_by_tag(self, tag: str) -> Dict[str, Dict[str, Any]]:
        return {
            model_id: meta
            for model_id, meta in self._registry.items()
            if tag in meta.get('tags', [])
        }
