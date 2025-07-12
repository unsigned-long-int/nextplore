from pydantic_settings import BaseSettings 

class Settings(BaseSettings):
    DATABASE_URL: str
    AZURE_CLIENT_ID: str
    AZURE_TENANT_ID: str
    JWT_AUDIENCE: str
    ISSUER: str
    JWKS_URL: str
    JWT_ALGORITHMS: str
    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_GROUP_PREFIX: str

    class Config:
        env_file ='../.env'

settings = Settings()