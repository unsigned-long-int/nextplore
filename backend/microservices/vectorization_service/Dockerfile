FROM python:3.13-slim

RUN groupadd -r nextplore-group \
    && useradd -r -g nextplore-group -m vectorization-service

USER root 

WORKDIR /app

COPY microservices/vectorization_service /app/
COPY messaging /app/messaging
COPY shared/contracts/vectorization_service /app/shared/contracts/vectorization_service
COPY shared/open_ai_client_loader /app/shared/open_ai_client_loader

RUN pip install --no-cache-dir -r requirements.txt 

USER vectorization-service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
