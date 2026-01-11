.PHONY: help venv fmt lint clean test install run all

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
	uv venv
	uv pip install -e ".[dev]"
	@echo ""
	@echo "Virtual environment created. Activate with:"
	@echo "  source .venv/bin/activate"

run:
	python3 -m uvicorn watersvc.app:app --reload

fmt:
	python3 -m ruff format src/ tests/ api/

lint:
	python3 -m ruff check src/ tests/ api/
	python3 -m mypy src/

test:
	python3 -m pytest

install:
	uv pip install -e ".[dev]"

clean:
	rm -rf .venv/
	rm -rf __pycache__/ .pytest_cache/ .ruff_cache/
	rm -rf build/ dist/ *.egg-info/ src/*.egg-info/
	find . -type f -name "*.pyc" -delete
	rm -rf .vercel/

ci: fmt lint test
