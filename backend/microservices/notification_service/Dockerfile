FROM python:3.13-slim

RUN groupadd -r nextplore-group \
    && useradd -r -g nextplore-group -m notification-service

ARG NEXTPLORE_SDK
COPY ${NEXTPLORE_SDK} /tmp/wheels/
RUN pip install --upgrade /tmp/wheels/*.whl  \
    && rm -rf /tmp/wheels

WORKDIR /app

COPY microservices/notification_service /app/

RUN pip install --no-cache-dir -r requirements.txt

USER notification-service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
