FROM python:3.13-slim

RUN groupadd -r nextplore-group \
    && useradd -r -g nextplore-group -m embedding-service

ARG NEXTPLORE_SDK
ARG KAFKA_MESSAGING
ARG SVC_EMBEDDING_CONTRACTS
COPY ${NEXTPLORE_SDK} /tmp/wheels/
COPY ${KAFKA_MESSAGING} /tmp/wheels/
COPY ${SVC_EMBEDDING_CONTRACTS} /tmp/wheels/

RUN pip install --upgrade /tmp/wheels/*.whl  \
    && rm -rf /tmp/wheels


WORKDIR /app

COPY microservices/embedding_service /app/
COPY schemas /app/schemas/
RUN pip install --no-cache-dir -r requirements.txt

USER embedding-service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
