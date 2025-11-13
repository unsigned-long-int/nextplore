from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    integration_base_url: str = 'http://integration_service:8001'
    embedding_base_url: str = 'http://embedding_service:8001'
    vector_base_url: str = 'http://vector_service:8001'
    ai_orm_context_base_url: str = 'http://ai_orm_context_service:8001'


settings = Settings()
