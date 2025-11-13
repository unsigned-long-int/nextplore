import unittest
import yaml
from unittest.mock import patch, mock_open
from pathlib import Path

from ai_orm_context_service.services.orm_context.models_registry import ModelsRegistry


VALID_YAML = '''
providers:
  openai:
    gpt-3.5-turbo:
      label: GPT-3.5 Turbo
      tags: ['chat', 'openai']
    gpt-4:
      label: GPT-4
      tags: ['chat', 'openai', 'premium']
  anthropic:
    claude-2:
      label: Claude 2
      tags: ['chat', 'claude']
'''

INVALID_YAML = 'invalid_yaml: [unclosed_list'

MALFORMED_YAML = '''
not_providers:
  some_value: 123
'''


class TestModelsRegistry(unittest.TestCase):

    @patch('builtins.open', new_callable=mock_open, read_data=VALID_YAML)
    @patch('pathlib.Path.exists', return_value=True)
    def test_load_registry_success(self, mock_exists, mock_open_file):
        registry = ModelsRegistry(config_path=Path('/fake/path/models_registry.yaml'))
        all_models = registry.all()

        self.assertIn('openai', all_models)
        self.assertIn('gpt-3.5-turbo', all_models['openai'])
        self.assertEqual(all_models['openai']['gpt-3.5-turbo']['label'], 'GPT-3.5 Turbo')

    @patch('builtins.open', new_callable=mock_open, read_data=VALID_YAML)
    @patch('pathlib.Path.exists', return_value=True)
    def test_list_models(self, mock_exists, mock_open_file):
        registry = ModelsRegistry(config_path=Path('/fake/path/models_registry.yaml'))
        models = registry.list_models()
        self.assertEqual(len(models), 3)
        self.assertTrue(any(m['provider'] == 'openai' and m['model_id'] == 'gpt-4' for m in models))

    @patch('builtins.open', new_callable=mock_open, read_data=VALID_YAML)
    @patch('pathlib.Path.exists', return_value=True)
    def test_get_model_success(self, mock_exists, mock_open_file):
        registry = ModelsRegistry(config_path=Path('/fake/path/models_registry.yaml'))
        model = registry.get_model('openai', 'gpt-4')
        self.assertEqual(model['label'], 'GPT-4')

    @patch('builtins.open', new_callable=mock_open, read_data=VALID_YAML)
    @patch('pathlib.Path.exists', return_value=True)
    def test_get_model_not_found(self, mock_exists, mock_open_file):
        registry = ModelsRegistry(config_path=Path('/fake/path/models_registry.yaml'))
        with self.assertRaises(ValueError):
            registry.get_model('openai', 'non-existent-model')

    @patch('builtins.open', new_callable=mock_open, read_data=VALID_YAML)
    @patch('pathlib.Path.exists', return_value=True)
    def test_get_by_tag(self, mock_exists, mock_open_file):
        registry = ModelsRegistry(config_path=Path('/fake/path/models_registry.yaml'))
        results = registry.get_by_tag('premium')
        self.assertIn('gpt-4', results)
        self.assertNotIn('gpt-3.5-turbo', results)

    @patch('pathlib.Path.exists', return_value=False)
    def test_file_not_found(self, mock_exists):
        with self.assertRaises(FileNotFoundError):
            ModelsRegistry(config_path=Path('/non/existent/file.yaml'))

    @patch('builtins.open', new_callable=mock_open, read_data=MALFORMED_YAML)
    @patch('pathlib.Path.exists', return_value=True)
    def test_invalid_yaml_format(self, mock_exists, mock_open_file):
        with self.assertRaises(ValueError):
            ModelsRegistry(config_path=Path('/fake/path/models_registry.yaml'))

    @patch('builtins.open', new_callable=mock_open, read_data=INVALID_YAML)
    @patch('pathlib.Path.exists', return_value=True)
    def test_yaml_parse_error(self, mock_exists, mock_open_file):
        with self.assertRaises(yaml.YAMLError):
            ModelsRegistry(config_path=Path('/fake/path/models_registry.yaml'))
