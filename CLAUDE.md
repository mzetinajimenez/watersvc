# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A backend-only FastAPI service deployed on Vercel using serverless functions. The root endpoint (`/`) redirects to `/docs` for immediate API documentation access via Swagger UI.

## Prerequisites

This project uses [uv](https://github.com/astral-sh/uv) for fast Python package management. Install it with:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Commands

### Make Commands (Recommended)
```bash
# Show help (default)
make
make help

# Create virtual environment
make venv

# Run development server with reload
make run

# Format code with ruff
make fmt

# Lint code with ruff and mypy
make lint

# Run tests with pytest
make test

# Install dependencies (when venv is active)
make install

# Clean temp files and venv
make clean

# Run fmt, lint, and test
make ci
```

### Manual Commands
```bash
# Install package with dev dependencies
uv pip install -e ".[dev]"

# Run local development server
python3 -m uvicorn watersvc.app:app --reload

# Run with Vercel CLI (production-like environment)
vercel dev

# Run tests
python3 -m pytest

# Format code
python3 -m ruff format src/ tests/ api/

# Lint code
python3 -m ruff check src/ tests/ api/
python3 -m mypy src/
```

## Architecture

### Package Structure
This project uses a **src-layout** structure with the package located at `src/watersvc/`:
- `src/watersvc/app.py` - FastAPI application instance and configuration
- `src/watersvc/routes.py` - API route handlers (APIRouter)
- `src/watersvc/__init__.py` - Package initialization, exports `app` and `__version__`

### Vercel Deployment Pattern
The project uses a **dual entry point pattern** for Vercel compatibility:
1. **Application package** (`src/watersvc/`) - Main application code
2. **Vercel entry point** (`api/index.py`) - Imports and exposes the app for Vercel's Python runtime

The `api/index.py` file serves as a shim that imports `watersvc.app:app` for Vercel to serve as a serverless function.

### Configuration
- `pyproject.toml` - Build system (Hatchling), dependencies, dev tools config (ruff, pytest)
- `vercel.json` - Vercel deployment configuration pointing to `api/index.py`

### API Routes
All API routes are prefixed with `/api`:
- `GET /api/data` - Returns sample data array (3 items)
- `GET /api/items/{item_id}` - Returns single item by ID
- `GET /` - Redirects to `/docs` (Swagger UI)
- `GET /docs` - Auto-generated Swagger UI
- `GET /redoc` - Auto-generated ReDoc documentation

Routes are defined in `src/watersvc/routes.py` using FastAPI's `APIRouter`, then included in the main app with the `/api` prefix.

### Testing
Tests use FastAPI's `TestClient` (HTTPX-based) defined in `tests/conftest.py` as a pytest fixture. All test files are in the `tests/` directory and follow the `test_*.py` naming convention.
