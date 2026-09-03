import unittest
from unittest.mock import MagicMock, patch

from llm_inference_service.services.models_gateway.model_providers.lite_llm_provider import (
    LiteLlmProvider,
)
from llm_inference_service.services.models_gateway.provider_factory.factory import (
    HFProviderFactory,
    OpenAIProviderFactory,
    ProviderFactoryBase,
)

HF_META = {
    "model_id": "hf-test-model",
    "hf_path": "meta-llama/Llama-3.1-8B-Instruct",
    "max_tokens": 8192,
    "hf_url": "https://router.huggingface.co/v1",
}

OPENAI_META = {
    "model_id": "gpt-4o",
}


class TestProviderFactoryBase(unittest.TestCase):
    def test_cannot_instantiate_abstract_base(self):
        with self.assertRaises(TypeError):
            ProviderFactoryBase(model_meta={})

    def test_concrete_subclass_stores_model_meta(self):
        class ConcreteFactory(ProviderFactoryBase):
            def create(self) -> LiteLlmProvider:
                return MagicMock()

        factory = ConcreteFactory(model_meta=HF_META)
        self.assertEqual(factory.model_meta, HF_META)


class TestHFProviderFactory(unittest.TestCase):
    def _make_factory(self, meta: dict | None = None) -> HFProviderFactory:
        return HFProviderFactory(meta or HF_META)

    @patch(
        "llm_inference_service.services.models_gateway.provider_factory.factory.HFProvider"
    )
    @patch(
        "llm_inference_service.services.models_gateway.provider_factory.factory.HFModel"
    )
    def test_creates_hf_model_with_correct_fields(
        self, mock_hf_model, mock_hf_provider
    ):
        mock_hf_model.return_value = MagicMock()
        mock_hf_provider.return_value = MagicMock()

        self._make_factory().create()

        mock_hf_model.assert_called_once_with(
            model_id="hf-test-model",
            hf_path="meta-llama/Llama-3.1-8B-Instruct",
            max_tokens=8192,
            hf_url="https://router.huggingface.co/v1",
        )

    @patch(
        "llm_inference_service.services.models_gateway.provider_factory.factory.HFProvider"
    )
    @patch(
        "llm_inference_service.services.models_gateway.provider_factory.factory.HFModel"
    )
    def test_passes_hf_model_to_provider(self, mock_hf_model, mock_hf_provider):
        hf_model_instance = MagicMock()
        mock_hf_model.return_value = hf_model_instance
        mock_hf_provider.return_value = MagicMock()

        self._make_factory().create()

        mock_hf_provider.assert_called_once_with(hf_model_instance)

    @patch(
        "llm_inference_service.services.models_gateway.provider_factory.factory.HFProvider"
    )
    @patch(
        "llm_inference_service.services.models_gateway.provider_factory.factory.HFModel"
    )
    def test_returns_hf_provider_instance(self, mock_hf_model, mock_hf_provider):
        mock_hf_model.return_value = MagicMock()
        provider_instance = MagicMock()
        mock_hf_provider.return_value = provider_instance

        result = self._make_factory().create()

        self.assertIs(result, provider_instance)

    @patch(
        "llm_inference_service.services.models_gateway.provider_factory.factory.HFProvider"
    )
    @patch(
        "llm_inference_service.services.models_gateway.provider_factory.factory.HFModel"
    )
    def test_missing_meta_keys_passed_as_none(self, mock_hf_model, mock_hf_provider):
        mock_hf_model.return_value = MagicMock()
        mock_hf_provider.return_value = MagicMock()

        HFProviderFactory({}).create()

        mock_hf_model.assert_called_once_with(
            model_id=None,
            hf_path=None,
            max_tokens=None,
            hf_url=None,
        )


class TestOpenAIProviderFactory(unittest.TestCase):
    def _make_factory(self, meta: dict | None = None) -> OpenAIProviderFactory:
        return OpenAIProviderFactory(meta or OPENAI_META)

    @patch(
        "llm_inference_service.services.models_gateway.provider_factory.factory.OpenAiProvider"
    )
    def test_creates_provider_with_model_id(self, mock_openai_provider):
        mock_openai_provider.return_value = MagicMock()

        self._make_factory().create()

        mock_openai_provider.assert_called_once_with(model_id="gpt-4o")

    @patch(
        "llm_inference_service.services.models_gateway.provider_factory.factory.OpenAiProvider"
    )
    def test_returns_openai_provider_instance(self, mock_openai_provider):
        provider_instance = MagicMock()
        mock_openai_provider.return_value = provider_instance

        result = self._make_factory().create()

        self.assertIs(result, provider_instance)

    @patch(
        "llm_inference_service.services.models_gateway.provider_factory.factory.OpenAiProvider"
    )
    def test_missing_model_id_passed_as_none(self, mock_openai_provider):
        mock_openai_provider.return_value = MagicMock()

        OpenAIProviderFactory({}).create()

        mock_openai_provider.assert_called_once_with(model_id=None)

    @patch(
        "llm_inference_service.services.models_gateway.provider_factory.factory.OpenAiProvider"
    )
    def test_ignores_irrelevant_meta_keys(self, mock_openai_provider):
        mock_openai_provider.return_value = MagicMock()

        OpenAIProviderFactory(
            {**OPENAI_META, "hf_path": "irrelevant", "hf_url": "irrelevant"}
        ).create()

        mock_openai_provider.assert_called_once_with(model_id="gpt-4o")
