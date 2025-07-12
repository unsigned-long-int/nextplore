FROM python:3.13-slim

RUN groupadd -r nextplore-group \
    && useradd -r -g nextplore-group -m orchestration-service

USER root 

WORKDIR /app

COPY nextplore-orchestrator /app/
COPY messaging /app/messaging
COPY shared  /app/shared

RUN pip install --no-cache-dir -r requirements.txt 

USER orchestration-service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]