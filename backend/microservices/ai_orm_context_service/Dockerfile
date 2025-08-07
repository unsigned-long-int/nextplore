FROM python:3.13-slim

RUN groupadd -r nextplore-group \
    && useradd -r -g nextplore-group -m ai-orm-context-service

ARG SHARED_TGZ
COPY ${SHARED_TGZ} /tmp/nextplore_shared.tar.gz
RUN pip install --upgrade /tmp/nextplore_shared.tar.gz && rm /tmp/nextplore_shared.tar.gz

WORKDIR /app

COPY microservices/ai_orm_context_service /app/
RUN pip install --no-cache-dir -r requirements.txt 

USER ai-orm-context-service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
