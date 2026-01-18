FROM python:3.13-slim

RUN groupadd -r nextplore-group \
    && useradd -r -g nextplore-group -m ai-orm-context-service

ARG NEXTPLORE_SDK
ARG SVC_AI_ORM_CONTEXT_CONTRACTS
COPY ${NEXTPLORE_SDK} /tmp/wheels/
COPY ${SVC_AI_ORM_CONTEXT_CONTRACTS} /tmp/wheels/
RUN pip install --upgrade /tmp/wheels/*.whl  \
    && rm -rf /tmp/wheels

WORKDIR /app

COPY microservices/ai_orm_context_service /app/

RUN pip install --no-cache-dir -r requirements.txt 

USER ai-orm-context-service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
