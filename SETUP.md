# Setup Guide

This guide will help you set up and run the User Management Service locally.

## Prerequisites

- Python 3.11+ (tested with Python 3.12)
- pip or poetry
- Docker Desktop (optional, for Cosmos DB Emulator)

## Installation

### Option 1: Using pip (Recommended for development)

```bash
# Install dependencies
pip install -r requirements.txt

# Install development dependencies (for testing and linting)
pip install -r requirements-dev.txt
```

### Option 2: Using Poetry

```bash
# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

## Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your configuration:
   ```bash
   # For local development with Cosmos DB Emulator
   COSMOSDB_ENDPOINT=https://localhost:8081
   COSMOSDB_KEY=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==
   
   # For Auth Service integration (optional)
   AUTH_SERVICE_URL=http://localhost:8001
   ```

### Using Cosmos DB Emulator (Optional)

If you want to test with a real database locally:

```bash
# Using Docker
docker pull mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator
docker run -p 8081:8081 -p 10251:10251 -p 10252:10252 -p 10253:10253 -p 10254:10254 \
  -e AZURE_COSMOS_EMULATOR_PARTITION_COUNT=10 \
  -e AZURE_COSMOS_EMULATOR_ENABLE_DATA_PERSISTENCE=true \
  mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator
```

## Running the Service

### Development Mode (with auto-reload)

```bash
# Using uvicorn directly
uvicorn app.main:app --reload --port 8002

# Or using the Python module
python -m uvicorn app.main:app --reload --port 8002

# Or using the main script
python -m app.main
```

The service will be available at:
- API: http://localhost:8002
- OpenAPI docs: http://localhost:8002/docs
- ReDoc: http://localhost:8002/redoc

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8002 --workers 4
```

## Testing

### Run all tests
```bash
pytest
```

### Run tests with coverage
```bash
pytest --cov=app
```

### Run tests with verbose output
```bash
pytest -v
```

### Run specific test file
```bash
pytest tests/unit/test_health.py -v
```

## Code Quality

### Format code with Black
```bash
black app/ tests/
```

### Lint with Ruff
```bash
ruff check app/ tests/
```

### Type check with mypy
```bash
mypy app/
```

## Verifying the Setup

1. **Check if the service is running:**
   ```bash
   curl http://localhost:8002/
   ```
   
   Expected response:
   ```json
   {
     "service": "User Management Service",
     "version": "0.1.0",
     "status": "running"
   }
   ```

2. **Check health status:**
   ```bash
   curl http://localhost:8002/health
   ```
   
   Expected response (when dependencies are not available):
   ```json
   {
     "status": "degraded",
     "service": "user-management-service",
     "version": "0.1.0",
     "dependencies": {
       "database": "unhealthy",
       "auth_service": "unavailable"
     }
   }
   ```

3. **Browse API documentation:**
   Open http://localhost:8002/docs in your browser

## Troubleshooting

### Port already in use
```bash
# Find process using port 8002
lsof -i :8002

# Kill the process
kill <PID>
```

### Cosmos DB connection errors
- Verify the emulator is running: `curl -k https://localhost:8081/`
- Check the endpoint and key in your `.env` file
- The service will start even if Cosmos DB is not available (graceful degradation)

### Auth Service connection errors
- Verify Auth Service is running: `curl http://localhost:8001/health`
- The service will start even if Auth Service is not available (graceful degradation)

## Next Steps

- See [README.md](./README.md) for detailed service documentation
- Review [docs/services/user-management/spec.md](./docs/services/user-management/spec.md) for API specifications
- Check [docs/architecture/api-guidelines.md](./docs/architecture/api-guidelines.md) for API design guidelines

## Development Workflow

1. Create a new branch from `main`
2. Make your changes
3. Run tests: `pytest`
4. Format code: `black app/ tests/`
5. Lint: `ruff check app/ tests/`
6. Commit and push
7. Create a pull request
