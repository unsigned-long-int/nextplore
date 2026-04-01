from nextplore_orchestrator.services.query_orchestrator.exceptions import LlmOrchestratorBootstrapError
from nextplore_orchestrator.services.query_orchestrator.llm_orchestrator.llm_orchestrator import (
    LlmOrchestrator,
    ExpandedLlmOrchestrator,
    SimpleLlmOrchestrator
)
from svc_nextplore_orchestrator_contracts.models import QueryMode

class LlmOrchestratorFactory:
    def __init__(
        self,
        expanded_llm_orchestrator: ExpandedLlmOrchestrator,
        simple_llm_orchestrator: SimpleLlmOrchestrator
    ) -> None:
        self._orchestrators = {
            QueryMode.EXPANDED: expanded_llm_orchestrator,
            QueryMode.SIMPLE: simple_llm_orchestrator
        }

    def get_llm_orchestrator(self, mode: QueryMode) -> LlmOrchestrator:
        llm_orchestrator = self._orchestrators.get(mode)
        if llm_orchestrator is None:
            raise LlmOrchestratorBootstrapError('LLM orchestrator is not supported')
        return llm_orchestrator
