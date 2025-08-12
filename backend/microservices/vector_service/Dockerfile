FROM python:3.13-slim

RUN groupadd -r nextplore-group \
    && useradd -r -g nextplore-group -m vector-upsert-service

ARG SHARED_TGZ
COPY ${SHARED_TGZ} /tmp/nextplore_sdk.tar.gz

RUN pip install /tmp/nextplore_sdk.tar.gz \
    && apt-get update && apt-get install -y \
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

COPY microservices/vector_service /app/
COPY messaging /app/messaging/

RUN pip install --no-cache-dir -r requirements.txt 

USER vector-upsert-service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
