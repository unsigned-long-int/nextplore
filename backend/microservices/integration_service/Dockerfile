FROM python:3.13-slim

RUN groupadd -r nextplore-group \
    && useradd -r -g nextplore-group -m integration-service

RUN apt-get update && apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gcc \
    gnupg \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && sh -c "curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -" \
    && apt-get update \
    && sh -c "curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list" \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && apt-get clean

WORKDIR /app


COPY microservices/integration_service /app/
COPY messaging /app/messaging
COPY shared/logging /app/shared/logging
COPY shared/identity_service/user_identity /app/shared/identity_service/user_identity
COPY shared/contracts/integration_service /app/shared/contracts/integration_service
COPY shared/database/sql_connection_service /app/shared/database/sql_connection_service
COPY shared/database/connection_builder /app/shared/database/connection_builder
COPY shared/database/dependencies /app/shared/database/dependencies
COPY shared/database/models /app/shared/database/models
COPY shared/database/crawler_factory /app/shared/database/crawler_factory
COPY shared/cache/client /app/shared/cache/client
COPY shared/cache/utils /app/shared/cache/utils
COPY shared/cache/service_caches/integration_cache /app/shared/cache/service_caches/integration_cache
COPY shared/encryptor /app/shared/encryptor


RUN pip install --no-cache-dir -r requirements.txt 

USER integration-service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
