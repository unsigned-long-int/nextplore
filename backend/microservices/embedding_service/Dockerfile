FROM python:3.13-slim

RUN groupadd -r nextplore-group \
    && useradd -r -g nextplore-group -m embedding-service

ARG SHARED_TGZ
COPY ${SHARED_TGZ} /tmp/nextplore_shared.tar.gz
RUN pip install --upgrade /tmp/nextplore_shared.tar.gz && rm /tmp/nextplore_shared.tar.gz

WORKDIR /app

COPY microservices/embedding_service /app/
COPY messaging /app/messaging
RUN pip install --no-cache-dir -r requirements.txt 

USER embedding-service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
