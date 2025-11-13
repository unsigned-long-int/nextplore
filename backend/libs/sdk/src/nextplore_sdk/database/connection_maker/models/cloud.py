from enum import Enum 


class Cloud(Enum):
    AWS = 'aws'
    AZURE = 'azure'
    GCP = 'gcp'
    SNOWFLAKE_MANAGED = 'snowflake_managed'
