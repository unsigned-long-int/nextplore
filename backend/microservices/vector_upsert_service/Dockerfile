FROM python:3.13-slim

RUN groupadd -r nextplore-group \
    && useradd -r -g nextplore-group -m vector-upsert-service

USER root 
RUN apt-get update && apt-get install -y \
    gcc \
    gnupg \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

COPY microservices/vector_upsert_service /app/
COPY messaging /app/messaging/
COPY shared/database/sql_connection_service /app/shared/database/sql_connection_service/

RUN pip install --no-cache-dir -r requirements.txt 

USER vector-upsert-service
CMD ["python", "main.py"]
