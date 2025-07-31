FROM python:3.13-slim

RUN groupadd -r nextplore-group \
    && useradd -r -g nextplore-group -m ai-orm-context-service

USER root 

WORKDIR /app

COPY microservices/ai_orm_context_service /app/
COPY shared/logging /app/shared/logging
COPY shared/identity_service/user_identity /app/shared/identity_service/user_identity
COPY shared/cache/service_caches/ai_orm_context_cache /app/shared/cache/service_caches/ai_orm_context_cache
COPY shared/cache/client /app/shared/cache/client
COPY shared/cache/utils /app/shared/cache/utils
COPY shared/contracts/ai_orm_context_service /app/shared/contracts/ai_orm_context_service
COPY shared/open_ai_client_loader /app/shared/open_ai_client_loader


RUN pip install --no-cache-dir -r requirements.txt 

USER ai-orm-context-service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
