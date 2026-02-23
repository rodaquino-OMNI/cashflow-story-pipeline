.PHONY: install test lint typecheck run watch clean help

PYTHON = python3
VENV = .venv

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Create venv and install all dependencies
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -e ".[dev]"
	@echo "Activate with: source $(VENV)/bin/activate"

test: ## Run test suite
	$(VENV)/bin/pytest tests/ -v --tb=short

test-cov: ## Run tests with coverage report
	$(VENV)/bin/pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

lint: ## Run linter (ruff)
	$(VENV)/bin/ruff check src/ tests/
	$(VENV)/bin/ruff format --check src/ tests/

lint-fix: ## Auto-fix lint issues
	$(VENV)/bin/ruff check --fix src/ tests/
	$(VENV)/bin/ruff format src/ tests/

typecheck: ## Run type checker (mypy)
	$(VENV)/bin/mypy src/

run: ## Run pipeline with sample data
	$(VENV)/bin/python -m src.main run --input data/sample/ --config austa --output reports/

run-no-ai: ## Run pipeline without AI analysis
	$(VENV)/bin/python -m src.main run --input data/sample/ --config austa --output reports/ --no-ai

watch: ## Watch ERP export folder for new files
	$(VENV)/bin/python -m src.main watch --folder /erp/exports/ --config austa --output reports/

validate: ## Validate configuration files
	$(VENV)/bin/python -m src.main validate --config austa

clean: ## Remove build artifacts and caches
	rm -rf $(VENV) build/ dist/ *.egg-info .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
