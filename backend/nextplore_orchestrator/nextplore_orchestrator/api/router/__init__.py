from .ai_queries_router import router as ai_queries_router
from .gen_models_router import router as gen_models_router
from .user_profile_router import router as user_profile_router
from .datastore_profiles_router import router as integration_profiles_router
from .create_datastore_router import router as create_integration_router
from .test_datastore_router import router as test_integration_router
from .vector_profiles_router import router as vector_profiles_router
from .user_stats_router import router as user_stats_router
from .update_datastore_router import router as update_integration_router
from .delete_datastore_router import router as delete_integration_router
from .cert_profiles_router import router as cert_profiles_router
from .create_cert_router import router as create_cert_router
from .description_enhancement_router import router as description_enhancement_router
from .create_user_llm_router import router as create_llm_model_router
from .user_llm_profiles_router import router as user_llm_profiles_router
from .test_user_llm_router import router as test_user_llm_router
from .register_router import router as register_router
from .email_token_verification_router import router as email_token_verification_router

__all__ = [
    'ai_queries_router', 'gen_models_router', 'user_profile_router', 'integration_profiles_router',
    'create_integration_router', 'test_integration_router', 'vector_profiles_router', 'user_stats_router',
    'update_integration_router', 'delete_integration_router', 'cert_profiles_router', 'create_cert_router',
    'description_enhancement_router', 'create_llm_model_router', 'user_llm_profiles_router', 'test_user_llm_router',
    'register_router', 'email_token_verification_router'
]