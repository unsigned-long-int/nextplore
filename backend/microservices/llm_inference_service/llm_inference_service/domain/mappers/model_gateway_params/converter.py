from llm_inference_service.domain.models.model_gateway_params import UserLlm

from svc_llm_inference_contracts.models import UserLlmTestRequest


def user_llm_from_dto(user_llm_test_request: UserLlmTestRequest) -> UserLlm:
    return UserLlm(
        model_id=user_llm_test_request.model_id,
        api_base=user_llm_test_request.api_base,
        connection_params=user_llm_test_request.connection_params,
        max_tokens=user_llm_test_request.max_tokens,
    )