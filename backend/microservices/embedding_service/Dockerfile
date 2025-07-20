FROM python:3.13-slim

RUN groupadd -r nextplore-group \
    && useradd -r -g nextplore-group -m embedding-service

USER root 

WORKDIR /app

COPY microservices/embedding_service /app/
COPY messaging /app/messaging
COPY shared/logging /app/shared/logging
COPY shared/cache/client /app/shared/cache/client
COPY shared/cache/utils /app/shared/cache/utils
COPY shared/cache/service_caches/embedding_cache /app/shared/cache/service_caches/embedding_cache
COPY shared/identity_service/user_identity /app/shared/identity_service/user_identity
COPY shared/contracts/embedding_service /app/shared/contracts/embedding_service
COPY shared/open_ai_client_loader /app/shared/open_ai_client_loader


RUN pip install --no-cache-dir -r requirements.txt 

USER embedding-service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
