.PHONY: help up down logs stats clean

SDK_PATH=./libs/sdk/src
MSG_PATH=./libs/messaging/src

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build-libs:
	@echo "Building nextplore_sdk..."
	@cd libs/sdk/ && python -m build -w -o ../.wheelhouse/
	@echo "Building kafka_messaging..."
	@cd libs/messaging/ && python -m build -w -o ../.wheelhouse/
	@cd libs/svc_integration_contracts/ && python -m build -w -o ../.wheelhouse/
	@echo "Building svc_integration_contracts..."
	@cd libs/svc_ai_orm_context_contracts/ && python -m build -w -o ../.wheelhouse/
	@echo "Building svc_ai_orm_context_contracts..."
	@cd libs/svc_embedding_contracts/ && python -m build -w -o ../.wheelhouse/
	@echo "Building svc_embedding_contracts..."
	@cd libs/svc_nextplore_orchestrator_contracts/ && python -m build -w -o ../.wheelhouse/
	@echo "Building svc_nextplore_orchestrator_contracts..."
	@cd libs/svc_vector_contracts/ && python -m build -w -o ../.wheelhouse/
	@echo "Building svc_vector_contracts..."
	@echo "Libraries built successfully in libs/.wheelhouse/"

check-libs:
	@echo "Checking for required wheel files..."
	@test -f libs/.wheelhouse/nextplore_sdk-0.1.0-py3-none-any.whl || \
		(echo "nextplore_sdk wheel not found. Run 'make build-libs' first" && exit 1)
	@test -f libs/.wheelhouse/kafka_messaging-0.1.0-py3-none-any.whl || \
		(echo "kafka_messaging wheel not found. Run 'make build-libs' first" && exit 1)
	@test -f libs/.wheelhouse/svc_ai_orm_context_contracts-0.1.0-py3-none-any.whl || \
		(echo "svc_ai_orm_context_contracts wheel not found. Run 'make build-libs' first" && exit 1)
	@test -f libs/.wheelhouse/svc_embedding_contracts-0.1.0-py3-none-any.whl || \
		(echo "svc_embedding_contracts wheel not found. Run 'make build-libs' first" && exit 1)
	@test -f libs/.wheelhouse/svc_integration_contracts-0.1.0-py3-none-any.whl || \
		(echo "svc_integration_contracts wheel not found. Run 'make build-libs' first" && exit 1)
	@test -f libs/.wheelhouse/svc_nextplore_orchestrator_contracts-0.1.0-py3-none-any.whl || \
		(echo "svc_nextplore_orchestrator_contracts wheel not found. Run 'make build-libs' first" && exit 1)
	@test -f libs/.wheelhouse/svc_vector_contracts-0.1.0-py3-none-any.whl || \
		(echo "svc_vector_contracts wheel not found. Run 'make build-libs' first" && exit 1)
	@echo "All required libraries are built"

run-tests: install-libs
	@echo "Running tests for ai_orm_context_service..."
	@cd microservices/ai_orm_context_service && python3 -m unittest discover -s . -p "test_*.py" -v || exit 1
	@echo ""
	@echo "Running tests for embedding_service..."
	@cd microservices/embedding_service && python3 -m unittest discover -s . -p "test_*.py" -v || exit 1
	@echo ""
	@echo "Running tests for integration_service..."
	@cd microservices/integration_service && python3 -m unittest discover -s . -p "test_*.py" -v || exit 1
	@echo ""
	@echo "Running tests for messaging library..."
	@cd libs/messaging && python3 -m unittest discover -s . -p "test_*.py" -v || exit 1
	@echo ""
	@echo "Running tests for sdk library..."
	@cd libs/sdk && python3 -m unittest discover -s . -p "test_*.py" -v || exit 1
	@echo ""
	@echo "All tests passed!"

clean-libs:
	@echo "Cleaning wheels..."
	@rm -rf libs/.wheelhouse/*.whl
	@echo "Wheel files removed"

install-libs: check-libs
	@pip install libs/.wheelhouse/nextplore_sdk-0.1.0-py3-none-any.whl
	@pip install libs/.wheelhouse/kafka_messaging-0.1.0-py3-none-any.whl
	@pip install libs/.wheelhouse/svc_ai_orm_context_contracts-0.1.0-py3-none-any.whl
	@pip install libs/.wheelhouse/svc_embedding_contracts-0.1.0-py3-none-any.whl
	@pip install libs/.wheelhouse/svc_integration_contracts-0.1.0-py3-none-any.whl
	@pip install libs/.wheelhouse/svc_nextplore_orchestrator_contracts-0.1.0-py3-none-any.whl
	@pip install libs/.wheelhouse/svc_vector_contracts-0.1.0-py3-none-any.whl

infra: check-libs
	docker compose up -d redis zookeeper kafka

dev-integration: infra
	docker compose --profile integration_service up

dev-embedding: infra
	docker compose --profile embedding_service up

dev-vector: infra
	docker compose --profile vector_service up

dev-ai:
	docker compose up -d redis
	docker compose --profile ai_orm_context_service up

dev-orchestration: infra
	docker compose --profile orchestration_service up

all:
	docker compose --profile all up

down:
	docker compose --profile all down

logs:
	docker compose logs -f

stats:
	docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.CPUPerc}}"

clean:
	docker compose --profile all down -v
	docker system prune -a

integration:
	docker compose up integration_service

embedding:
	docker compose up embedding_service

vector:
	docker compose up vector_service

ai-orm:
	docker compose up ai_orm_context_service

orchestration:
	docker compose up orchestration_service

watch:
	watch -n 2 'docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}"'