.PHONY: help up down logs stats clean

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build-libs:
	@echo "Building nextplore_sdk..."
	@cd libs/sdk/ && python -m build -w -o ../.wheelhouse/
	@echo "Building kafka_messaging..."
	@cd libs/messaging/ && python -m build -w -o ../.wheelhouse/
	@echo "Libraries built successfully in libs/.wheelhouse/"

check-libs:
	@echo "Checking for required wheel files..."
	@test -f libs/.wheelhouse/nextplore_sdk-0.1.0-py3-none-any.whl || \
		(echo "nextplore_sdk wheel not found. Run 'make build-libs' first" && exit 1)
	@test -f libs/.wheelhouse/kafka_messaging-0.1.0-py3-none-any.whl || \
		(echo "kafka_messaging wheel not found. Run 'make build-libs' first" && exit 1)
	@echo "All required libraries are built"

run-tests:
	@PYTHONPATH="/Users/nik/personal_projects/nextplore/backend/libs/sdk/src" python3 -m unittest discover "microservices/ai_orm_context_service"

clean-libs:
	@echo "Cleaning wheels..."
	@rm -rf libs/.wheelhouse/*.whl
	@echo "Wheel files removed"

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