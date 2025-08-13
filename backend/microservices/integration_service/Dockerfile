FROM python:3.13-slim-bookworm

RUN groupadd -r nextplore-group \
    && useradd -r -g nextplore-group -m integration-service

ARG SHARED_TGZ
COPY ${SHARED_TGZ} /tmp/nextplore_sdk.tar.gz

ARG DEBIAN_FRONTEND=noninteractive
RUN pip install --no-cache-dir /tmp/nextplore_sdk.tar.gz \
    && rm /tmp/nextplore_sdk.tar.gz \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    gcc \
    libpq-dev \
    unixodbc-dev \
    build-essential \
    && curl -fsSLo /tmp/packages-microsoft-prod.deb \
    https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb \
    && dpkg -i /tmp/packages-microsoft-prod.deb \
    && rm /tmp/packages-microsoft-prod.deb \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
    msodbcsql18 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app


COPY microservices/integration_service /app/
COPY messaging /app/messaging

RUN pip install --no-cache-dir -r requirements.txt 

USER integration-service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
