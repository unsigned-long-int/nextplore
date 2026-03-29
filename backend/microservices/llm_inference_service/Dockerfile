FROM python:3.13-slim

RUN groupadd -r nextplore-group \
    && useradd -r -g nextplore-group -m llm-inference-service

ARG NEXTPLORE_SDK
ARG SVC_LLM_INFERENCE_CONTRACTS
COPY ${NEXTPLORE_SDK} /tmp/wheels/
COPY ${SVC_LLM_INFERENCE_CONTRACTS} /tmp/wheels/
RUN pip install --upgrade /tmp/wheels/*.whl  \
    && rm -rf /tmp/wheels

WORKDIR /app

COPY microservices/llm_inference_service /app/

RUN pip install --no-cache-dir -c constraints.txt -r requirements.txt

USER llm-inference-service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
