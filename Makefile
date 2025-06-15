.PHONY: install lint format test clean help

help:  ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:  ## Install dependencies using uv sync
	uv sync

lint:  ## Run ruff linting with fixes
	uv run ruff check src tests --fix --extend-select I --unsafe-fixes

format:  ## Format code using ruff
	uv run ruff format src tests

test:  ## Run tests with pytest
	uv run pytest tests -v

clean:  ## Clean up Python cache files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +

run:  ## Run the CLI tool (requires NOTION_API_KEY env var)
	uv run notion-to-json

dev:  ## Run lint, format, and test
	$(MAKE) lint
	$(MAKE) format
	$(MAKE) test