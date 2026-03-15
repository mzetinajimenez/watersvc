VENV   ?= .venv
PYTHON ?= $(VENV)/bin/python3

.PHONY: help venv fmt lint clean test integration install run all ci

# Default target
help:
	@echo "Available commands:"
	@echo "  make help    - Show this help message"
	@echo "  make venv    - Create virtual environment and install dependencies"
	@echo "  make run     - Run local development server with reload"
	@echo "  make fmt     - Format code with ruff"
	@echo "  make lint    - Lint code with ruff and mypy"
	@echo "  make test    - Run tests with pytest"
	@echo "  make install - Install package with dev dependencies"
	@echo "  make clean   - Remove venv and temporary files"
	@echo "  make ci      - Run fmt, lint, and test"

venv:
	uv venv $(VENV)
	uv pip install -e ".[dev]"
	@echo ""
	@echo "Virtual environment created. Activate with:"
	@echo "  source $(VENV)/bin/activate"

run:
	$(PYTHON) -m uvicorn watersvc.app:app --reload

fmt:
	$(PYTHON) -m ruff format src/ tests/ api/

lint:
	$(PYTHON) -m ruff check src/ tests/ api/
	$(PYTHON) -m mypy src/

test:
	$(PYTHON) -m pytest $(ARGS)

integration:
	$(PYTHON) -m pytest -m integration -v $(ARGS)

install:
	uv pip install -e ".[dev]"

clean:
	rm -rf $(VENV)/
	rm -rf __pycache__/ .pytest_cache/ .ruff_cache/
	rm -rf build/ dist/ *.egg-info/ src/*.egg-info/
	find . -type f -name "*.pyc" -delete
	rm -rf .vercel/

ci: fmt lint test integration
