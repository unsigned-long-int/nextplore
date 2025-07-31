import logging
from instructor import patch
from transformers import pipelines, AutoTokenizer, AutoModelForCausalLM

from services.context_providers.base import AIORMContextProviderBase
from services.context_schema import ORMContext
from shared.contracts.ai_orm_context_service import ORMContextRequest, ORMContextResponse
from .orm_request_schema_factory import get_orm_request_schema

logger = logging.getLogger(__name__)


class ModelInitialisationFailed(Exception):
    pass


class HuggingFaceORMContextProvider(AIORMContextProviderBase):
    def __init__(self, model_id: str, max_tokens: int = 512) -> None:
        self.model_id = model_id
        self.max_tokens = max_tokens

    def _init_model(self) -> None:
        try:
            tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            model = AutoModelForCausalLM.from_pretrained(self.model_id, device_map='auto')
            pipe = pipelines('text-generation', model=model, tokenizer=tokenizer, max_new_tokens=512)

            self.llm = patch(pipe)
            logger.info(f'HuggingFace pipeline loaded for model: {self.model_id}')
        except Exception as e:
            logger.error(f'Failed to initialize HuggingFace pipeline. Error: {e}', exc_info=True)
            raise ModelInitialisationFailed from e

    async def retrieve_orm_request(self, orm_context_request: ORMContextRequest) -> ORMContextResponse:
        system_prompt = f'''
        You are an ORM generator 
        Based on the user query, and the available metadata, 
        output the structured ORM request using the schema FunctionCall.
        Context:\n {orm_context_request.integration_registry_repr} 
        '''

        full_prompt =  f'{system_prompt.strip()}\nQuery: {orm_context_request.query.strip()}'
        FunctionCall = get_orm_request_schema(orm_context_request)

        structured = self.llm(full_prompt, FunctionCall)
        orm_context = ORMContext(
            integration=structured.integration_id,
            schema_name=structured.schema_name,
            class_name=structured.class_name,
            table_name=structured.table_name,
            column_names=structured.column_names,
            column_aggregates=structured.column_aggregates,
            column_filters=structured.column_filters
        )
        return orm_context
    