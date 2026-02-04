FROM python:3.13-slim-bookworm

RUN groupadd -r nextplore-group \
    && useradd -r -g nextplore-group -m orchestration-service

ARG NEXTPLORE_SDK
ARG KAFKA_MESSAGING
ARG SVC_AI_ORM_CONTEXT_CONTRACTS
ARG SVC_EMBEDDING_CONTRACTS
ARG SVC_INTEGRATION_CONTRACTS
ARG SVC_NEXTPLORE_ORCHESTRATOR_CONTRACTS
ARG SVC_VECTOR_CONTRACTS
COPY ${NEXTPLORE_SDK} /tmp/wheels/
COPY ${KAFKA_MESSAGING} /tmp/wheels/
COPY ${SVC_AI_ORM_CONTEXT_CONTRACTS} /tmp/wheels/
COPY ${SVC_EMBEDDING_CONTRACTS} /tmp/wheels/
COPY ${SVC_INTEGRATION_CONTRACTS} /tmp/wheels/
COPY ${SVC_NEXTPLORE_ORCHESTRATOR_CONTRACTS} /tmp/wheels/
COPY ${SVC_VECTOR_CONTRACTS} /tmp/wheels/
RUN pip install --upgrade /tmp/wheels/*.whl \
    && rm -rf /tmp/wheels

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    gnupg \
    gcc \
    libpq-dev \
    unixodbc-dev \
    && curl -fsSL --proto '=https' --tlsv1.2 \
    https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb \
    -o /tmp/packages-microsoft-prod.deb \
    && dpkg -i /tmp/packages-microsoft-prod.deb \
    && rm /tmp/packages-microsoft-prod.deb \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
    msodbcsql18 \
    && curl -fsSL --proto '=https' --tlsv1.2 \
    https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem \
    -o /usr/local/share/ca-certificates/aws-rds-global.crt \
    && chmod 0644 /usr/local/share/ca-certificates/aws-rds-global.crt \
    && curl -fsSL --proto '=https' --tlsv1.2 \
    https://storage.googleapis.com/cloudsql-ca-bundles/global.pem \
    -o /usr/local/share/ca-certificates/gcp-global.crt \
    && chmod 0644 /usr/local/share/ca-certificates/gcp-global.crt \
    && update-ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY nextplore_orchestrator /app/
COPY schemas /app/schemas/

RUN pip install --no-cache-dir -r requirements.txt 

USER orchestration-service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]