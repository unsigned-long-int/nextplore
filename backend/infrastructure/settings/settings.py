from pydantic_settings import BaseSettings 

class Settings(BaseSettings):
    DATABASE_URL: str

    AZURE_CLIENT_ID: str
    AZURE_CLIENT_SECRET: str
    AZURE_TENANT_ID: str
    JWT_AUDIENCE: str
    JWT_ALGORITHMS: str

    class Config:
        env_file ='../.env'

settings = Settings()