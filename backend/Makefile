.PHONY: help up down logs stats clean

SDK_PATH=./libs/sdk/src
MSG_PATH=./libs/messaging/src
PYTHON := python3
TEST_PATTERN := test_*.py
COVERAGE_MIN := 80

AI_SERVICE := microservices/llm_inference_service
EMBEDDING_SERVICE := microservices/embedding_service
INTEGRATION_SERVICE := microservices/integration_service
VECTOR_SERVICE := microservices/vector_service
MESSAGING_LIB := libs/messaging
SDK_LIB := libs/sdk

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build-libs:
	@echo "Building nextplore_sdk..."
	@cd libs/sdk/ && python -m build -w -o ../.wheelhouse/
	@echo "Building kafka_messaging..."
	@cd libs/messaging/ && python -m build -w -o ../.wheelhouse/
	@cd libs/svc_integration_contracts/ && python -m build -w -o ../.wheelhouse/
	@echo "Building svc_integration_contracts..."
	@cd libs/svc_llm_inference_contracts/ && python -m build -w -o ../.wheelhouse/
	@echo "Building svc_llm_inference_contracts..."
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
	@test -f libs/.wheelhouse/svc_llm_inference_contracts-0.1.0-py3-none-any.whl || \
		(echo "svc_llm_inference_contracts wheel not found. Run 'make build-libs' first" && exit 1)
	@test -f libs/.wheelhouse/svc_embedding_contracts-0.1.0-py3-none-any.whl || \
		(echo "svc_embedding_contracts wheel not found. Run 'make build-libs' first" && exit 1)
	@test -f libs/.wheelhouse/svc_integration_contracts-0.1.0-py3-none-any.whl || \
		(echo "svc_integration_contracts wheel not found. Run 'make build-libs' first" && exit 1)
	@test -f libs/.wheelhouse/svc_nextplore_orchestrator_contracts-0.1.0-py3-none-any.whl || \
		(echo "svc_nextplore_orchestrator_contracts wheel not found. Run 'make build-libs' first" && exit 1)
	@test -f libs/.wheelhouse/svc_vector_contracts-0.1.0-py3-none-any.whl || \
		(echo "svc_vector_contracts wheel not found. Run 'make build-libs' first" && exit 1)
	@echo "All required libraries are built"

install-test-deps:
	@echo "Installing coverage..."
	@pip install coverage --break-system-packages
	@echo "Coverage installed"

run-tests: install-libs
	@echo "Running tests for llm_inference_service..."
	@cd $(AI_SERVICE) && $(PYTHON) -m unittest discover -s . -p "$(TEST_PATTERN)" -v || exit 1
	@echo ""
	@echo "Running tests for embedding_service..."
	@cd $(EMBEDDING_SERVICE) && $(PYTHON) -m unittest discover -s . -p "$(TEST_PATTERN)" -v || exit 1
	@echo ""
	@echo "Running tests for integration_service..."
	@cd $(INTEGRATION_SERVICE) && $(PYTHON) -m unittest discover -s . -p "$(TEST_PATTERN)" -v || exit 1
	@echo ""
	@echo "Running tests for vector_service..."
	cd $(VECTOR_SERVICE) && $(PYTHON) -m unittest discover -s . -p "$(TEST_PATTERN)" -v || exit 1
	@echo ""
	@echo "Running tests for messaging library..."
	@cd $(MESSAGING_LIB) && $(PYTHON) -m unittest discover -s . -p "$(TEST_PATTERN)" -v || exit 1
	@echo ""
	@echo "Running tests for sdk library..."
	@cd $(SDK_LIB) && $(PYTHON) -m unittest discover -s . -p "$(TEST_PATTERN)" -v || exit 1
	@echo ""
	@echo "All tests passed!"

run-tests-cov: install-libs install-test-deps
	@echo "Running tests with coverage..."
	@rm -f .coverage .coverage.*
	@echo ""
	@echo "Testing ai_orm_context_service..."
	@cd $(AI_SERVICE) && $(PYTHON) -m coverage run --source=. --omit="test_*.py,*/tests/*,*/__pycache__/*" -m unittest discover -s . -p "$(TEST_PATTERN)" -v || exit 1
	@mv $(AI_SERVICE)/.coverage .coverage.ai 2>/dev/null || true
	@echo ""
	@echo "Testing embedding_service..."
	@cd $(EMBEDDING_SERVICE) && $(PYTHON) -m coverage run --source=. --omit="test_*.py,*/tests/*,*/__pycache__/*" -m unittest discover -s . -p "$(TEST_PATTERN)" -v || exit 1
	@mv $(EMBEDDING_SERVICE)/.coverage .coverage.embedding 2>/dev/null || true
	@echo ""
	@echo "Testing integration_service..."
	@cd $(INTEGRATION_SERVICE) && $(PYTHON) -m coverage run --source=. --omit="test_*.py,*/tests/*,*/__pycache__/*" -m unittest discover -s . -p "$(TEST_PATTERN)" -v || exit 1
	@mv $(INTEGRATION_SERVICE)/.coverage .coverage.integration 2>/dev/null || true
	@echo ""
	@echo "Testing vector_service..."
	@cd $(VECTOR_SERVICE) && $(PYTHON) -m coverage run --source=. --omit="test_*.py,*/tests/*,*/__pycache__/*" -m unittest discover -s . -p "$(TEST_PATTERN)" -v || exit 1
	@mv $(VECTOR_SERVICE)/.coverage .coverage.vector 2>/dev/null || true
	@echo ""
	@echo "Testing messaging library..."
	@cd $(MESSAGING_LIB) && PYTHONPATH=src $(PYTHON) -m coverage run --source=$$(pwd)/src --omit="test_*.py,*/tests/*,*/__pycache__/*" -m unittest discover -s tests -p "$(TEST_PATTERN)" -t . -v || exit 1
	@mv $(MESSAGING_LIB)/.coverage .coverage.messaging 2>/dev/null || true
	@echo ""
	@echo "Testing sdk library..."
	@cd $(SDK_LIB) && PYTHONPATH=src $(PYTHON) -m coverage run --source=$$(pwd)/src --omit="test_*.py,*/tests/*,*/__pycache__/*" -m unittest discover -s tests -p "$(TEST_PATTERN)" -t . -v || exit 1
	@mv $(SDK_LIB)/.coverage .coverage.sdk 2>/dev/null || true
	@echo ""
	@echo "Combining coverage data..."
	@$(PYTHON) -m coverage combine .coverage.*
	@echo ""
	@echo "Coverage Report:"
	@$(PYTHON) -m coverage report --skip-covered
	@$(PYTHON) -m coverage html -d htmlcov
	@$(PYTHON) -m coverage xml -o coverage.xml
	@echo ""
	@echo "Checking coverage threshold (minimum: $(COVERAGE_MIN)%)..."
	@$(PYTHON) -m coverage report --fail-under=$(COVERAGE_MIN) || \
		(echo "Coverage below $(COVERAGE_MIN)%" && exit 1)
	@echo ""
	@echo "All tests passed with coverage!"
	@echo "HTML report: htmlcov/index.html"
	@echo "XML report: coverage.xml"

test-ai: install-libs
	@echo "Running tests for llm_inference_service..."
	@cd $(AI_SERVICE) && $(PYTHON) -m unittest discover -s . -p "$(TEST_PATTERN)" -v

test-embedding: install-libs
	@echo "Running tests for embedding_service..."
	@cd $(EMBEDDING_SERVICE) && $(PYTHON) -m unittest discover -s . -p "$(TEST_PATTERN)" -v

test-integration: install-libs
	@echo "Running tests for integration_service..."
	@cd $(INTEGRATION_SERVICE) && $(PYTHON) -m unittest discover -s . -p "$(TEST_PATTERN)" -v

test-vector: install-libs
	@echo "Running tests for vector_service..."
	cd $(VECTOR_SERVICE) && $(PYTHON) -m unittest discover -s . -p "$(TEST_PATTERN)" -v

test-messaging: install-libs
	@echo "Running tests for messaging library..."
	@cd $(MESSAGING_LIB) && $(PYTHON) -m unittest discover -s . -p "$(TEST_PATTERN)" -v

test-sdk: install-libs
	@echo "Running tests for sdk library..."
	@cd $(SDK_LIB) && $(PYTHON) -m unittest discover -s . -p "$(TEST_PATTERN)" -v

test-ai-cov: install-libs install-test-deps
	@cd $(AI_SERVICE) && $(PYTHON) -m coverage run --source=. --omit="test_*.py" -m unittest discover -s . -p "$(TEST_PATTERN)" -v
	@cd $(AI_SERVICE) && $(PYTHON) -m coverage report
	@cd $(AI_SERVICE) && $(PYTHON) -m coverage html

test-embedding-cov: install-libs install-test-deps
	@cd $(EMBEDDING_SERVICE) && $(PYTHON) -m coverage run --source=. --omit="test_*.py" -m unittest discover -s . -p "$(TEST_PATTERN)" -v
	@cd $(EMBEDDING_SERVICE) && $(PYTHON) -m coverage report
	@cd $(EMBEDDING_SERVICE) && $(PYTHON) -m coverage html

test-integration-cov: install-libs install-test-deps
	@cd $(INTEGRATION_SERVICE) && $(PYTHON) -m coverage run --source=. --omit="test_*.py" -m unittest discover -s . -p "$(TEST_PATTERN)" -v
	@cd $(INTEGRATION_SERVICE) && $(PYTHON) -m coverage report
	@cd $(INTEGRATION_SERVICE) && $(PYTHON) -m coverage html

test-messaging-cov: install-libs install-test-deps
	@cd $(MESSAGING_LIB) && $(PYTHON) -m coverage run --source=. --omit="test_*.py" -m unittest discover -s . -p "$(TEST_PATTERN)" -v
	@cd $(MESSAGING_LIB) && $(PYTHON) -m coverage report
	@cd $(MESSAGING_LIB) && $(PYTHON) -m coverage html

test-sdk-cov: install-libs install-test-deps
	@cd $(SDK_LIB) && $(PYTHON) -m coverage run --source=. --omit="test_*.py" -m unittest discover -s . -p "$(TEST_PATTERN)" -v
	@cd $(SDK_LIB) && $(PYTHON) -m coverage report
	@cd $(SDK_LIB) && $(PYTHON) -m coverage html

clean-libs:
	@echo "Cleaning wheels..."
	@rm -rf libs/.wheelhouse/*.whl
	@echo "Wheel files removed"

clean-coverage:
	@echo "Cleaning coverage data..."
	@rm -rf htmlcov .coverage* __pycache__
	@find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name ".coverage*" -delete 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -f coverage.xml
	@echo "Coverage data cleaned"

install-libs: check-libs
	@echo "Installing libraries..."
	@pip install libs/.wheelhouse/nextplore_sdk-0.1.0-py3-none-any.whl
	@pip install libs/.wheelhouse/kafka_messaging-0.1.0-py3-none-any.whl
	@pip install libs/.wheelhouse/svc_llm_inference_contracts-0.1.0-py3-none-any.whl
	@pip install libs/.wheelhouse/svc_embedding_contracts-0.1.0-py3-none-any.whl
	@pip install libs/.wheelhouse/svc_integration_contracts-0.1.0-py3-none-any.whl
	@pip install libs/.wheelhouse/svc_nextplore_orchestrator_contracts-0.1.0-py3-none-any.whl
	@pip install libs/.wheelhouse/svc_vector_contracts-0.1.0-py3-none-any.whl
	@echo "Libraries installed"

uninstall-libs:
	@echo "Uninstalling libraries..."
	@pip uninstall -y nextplore_sdk kafka_messaging svc_llm_inference_contracts \
		svc_embedding_contracts svc_integration_contracts \
		svc_nextplore_orchestrator_contracts svc_vector_contracts 2>/dev/null || true
	@echo "Libraries uninstalled"

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
	docker compose --profile llm_inference_service up

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
	docker system prune -a --volumes

integration:
	docker compose up integration_service

embedding:
	docker compose up embedding_service

vector:
	docker compose up vector_service

llm-inference:
	docker compose up llm_inference_service

orchestration:
	docker compose up orchestration_service

watch:
	watch -n 2 'docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}"'


INFRA_PROFILES := --profile kafka --profile redis --profile zookeeper

rebuild-integration: infra
	docker compose --profile integration_service $(INFRA_PROFILES) rm -f integration_service
	docker compose --profile integration_service $(INFRA_PROFILES) up -d --build integration_service

rebuild-embedding: infra
	docker compose --profile embedding_service $(INFRA_PROFILES) rm -f embedding_service
	docker compose --profile embedding_service $(INFRA_PROFILES) up -d --build embedding_service

rebuild-vector: infra
	docker compose --profile vector_service $(INFRA_PROFILES) rm -f vector_service
	docker compose --profile vector_service $(INFRA_PROFILES) up -d --build vector_service

rebuild-llm-inference: infra
	docker compose --profile llm_inference_service $(INFRA_PROFILES) rm -f llm_inference_service
	docker compose --profile llm_inference_service $(INFRA_PROFILES) up -d --build llm_inference_service

rebuild-orchestration: infra
	docker compose --profile orchestration_service $(INFRA_PROFILES) rm -f orchestration_service
	docker compose --profile orchestration_service $(INFRA_PROFILES) up -d --build orchestration_service
