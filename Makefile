PYTHON := python3
WHEELHOUSE := backend/libs/.wheelhouse
PKGS := libs/sdk libs/messaging

.PHONY: all wheels install test clean

all: wheels

wheels:
	@mkdir -p $(WHEELHOUSE)
	@for pkg in $(PKGS); do \
		echo "Building $$pkg"; \
		$(PYTHON) -m build -w -o $(WHEELHOUSE) $$pkg; \
	done


install: wheels
	@$(PYTHON) -m pip install --no-index --find-links $(WHEELHOUSE) sdk messaging

unittest: install
	@$(RUN)/python -m unittest discover -s microservices/ai_orm_context_service
	@$(RUN)/python -m unittest discover -s microservices/embedding_service
	@$(RUN)/python -m unittest discover -s libs/messaging
	@$(RUN)/python -m unittest discover -s libs/sdk

clean:
	@rm -rf $(PYTHON) $(WHEELHOUSE) **/*.egg-info **/*.dist-info **/__pycache__ build dist .pytest_cache