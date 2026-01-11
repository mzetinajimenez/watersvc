[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fvercel%2Fexamples%2Ftree%2Fmain%2Fpython%2Ffastapi&demo-title=FastAPI&demo-description=Use%20FastAPI%20on%20Vercel%20with%20Serverless%20Functions%20using%20the%20Python%20Runtime.&demo-url=https%3A%2F%2Fvercel-plus-fastapi.vercel.app%2F&demo-image=https://assets.vercel.com/image/upload/v1669994600/random/python.png)

# FastAPI + Vercel

This example shows how to use FastAPI on Vercel with Serverless Functions using the [Python Runtime](https://vercel.com/docs/concepts/functions/serverless-functions/runtimes/python).

## Demo

https://vercel-plus-fastapi.vercel.app/

## How it Works

This example uses the Asynchronous Server Gateway Interface (ASGI) with FastAPI to enable handling requests on Vercel with Serverless Functions.

## Development Setup

### Quick Start with Make

This project includes a Makefile for convenient development commands:

```bash
# Show all available commands
make

# Create virtual environment and install dependencies
make venv

# Activate the virtual environment
source .venv/bin/activate

# Run development server with hot reload
make run

# Format code
make fmt

# Lint code
make lint

# Run tests
make test

# Clean temporary files
make clean
```

### Manual Setup

**Install Dependencies:**

```bash
# Install package in editable mode with dev dependencies
pip install -e ".[dev]"
```

**Running Locally:**

Option 1: Using uvicorn (recommended for development)

```bash
uvicorn watersvc.app:app --reload
```

Your FastAPI application is now available at `http://localhost:8000`. Visit `http://localhost:8000/docs` for interactive API documentation.

Option 2: Using Vercel CLI (production-like environment)

```bash
npm i -g vercel
vercel dev
```

Your FastAPI application is now available at `http://localhost:3000`.

**Running Tests:**

```bash
pytest
```

**Linting and Formatting:**

```bash
# Check for linting issues
ruff check src/

# Format code
ruff format src/

# Type check with mypy
mypy src/
```

## One-Click Deploy

Deploy the example using [Vercel](https://vercel.com?utm_source=github&utm_medium=readme&utm_campaign=vercel-examples):

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fvercel%2Fexamples%2Ftree%2Fmain%2Fpython%2Ffastapi&demo-title=FastAPI&demo-description=Use%20FastAPI%20on%20Vercel%20with%20Serverless%20Functions%20using%20the%20Python%20Runtime.&demo-url=https%3A%2F%2Fvercel-plus-fastapi.vercel.app%2F&demo-image=https://assets.vercel.com/image/upload/v1669994600/random/python.png)
