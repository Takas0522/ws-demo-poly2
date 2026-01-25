# User Management Service (テナント管理サービス)

User Management Service for ws-demo-poly2 project.

## Overview

This service manages tenants and tenant-associated users. It distinguishes between privileged tenants and regular tenants, providing role-based access control.

## Features

- Tenant management (CRUD operations)
- User-tenant relationship management
- Role-based access control (全体管理者, 管理者, 閲覧者)
- Privileged tenant protection
- FastAPI web framework
- Azure Cosmos DB integration

## Documentation

### Service Documentation
- [Service Specification](./docs/services/user-management/spec.md) - Complete service specification including user scenarios, API endpoints, and business logic
- [Data Model](./docs/services/user-management/data-model.md) - Cosmos DB schema and data structure

### Architecture Documentation
- [API Guidelines](./docs/architecture/api-guidelines.md) - REST API design standards
- [Authentication Flow](./docs/architecture/authentication-flow.md) - JWT-based authentication and authorization
- [Database Design](./docs/architecture/database-design.md) - Cosmos DB container design and partition strategy

## Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| 全体管理者 | System-wide administrator | Can operate on all tenants including privileged tenants |
| 管理者 | Regular tenant administrator | Can add, delete, and edit regular tenants |
| 閲覧者 | Read-only user | Can only view tenant information |

## Privileged Tenant

Privileged tenants have special constraints:
- **Cannot be deleted**: At least one must exist in the system
- **Cannot be edited**: Basic information like tenant name cannot be changed
- **User management restriction**: Only users with "全体管理者" role can add/remove users

## Setup

### Prerequisites

- Python 3.11+
- Azure Cosmos DB account
- Docker Desktop (v20.10+) - for Cosmos DB Emulator

### Installation

```bash
# Install dependencies using pip
pip install -r requirements.txt

# Or using poetry
poetry install
```

### Configuration

Copy `.env.example` to `.env` and configure your settings:

```bash
cp .env.example .env
```

Required environment variables:
- `COSMOSDB_ENDPOINT`: Your Cosmos DB endpoint URL
- `COSMOSDB_KEY`: Your Cosmos DB access key
- `COSMOSDB_DATABASE`: Database name (default: management-app)
- `COSMOSDB_CONTAINERS`: Container names for tenants and tenant-users

## Running the Service

### Development Mode

```bash
# Using uvicorn directly
uvicorn app.main:app --reload --port 8002

# Or using the startup script
python -m app.main
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8002
```

## API Endpoints

Base URL: `http://localhost:8002`

### Health Check
- `GET /health` - Service health status

### Tenants
- `GET /api/tenants` - List all tenants
- `GET /api/tenants/{tenantId}` - Get tenant details
- `POST /api/tenants` - Create new tenant
- `PUT /api/tenants/{tenantId}` - Update tenant
- `DELETE /api/tenants/{tenantId}` - Delete tenant (not allowed for privileged tenants)

### Tenant Users
- `GET /api/tenants/{tenantId}/users` - List users in tenant
- `POST /api/tenants/{tenantId}/users` - Add user to tenant
- `DELETE /api/tenants/{tenantId}/users/{userId}` - Remove user from tenant

## Database Schema

### Containers

- `tenants` - Tenant information (Partition key: `/id`)
- `tenant-users` - Tenant-user relationships (Partition key: `/tenantId`)

See [Data Model documentation](./docs/services/user-management/data-model.md) for detailed schema.

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app
```

### Seeding Data

```bash
# Run data seeding script
python scripts/seed_data.py
```

## Related Services

- **Auth Service** (ws-demo-poly3) - Provides authentication and authorization
- **Service Setting Service** (ws-demo-poly4) - Manages service assignments to tenants
- **Frontend** (ws-demo-poly1) - Web UI for the management application

## License

This project is part of the ws-demo-poly workspace.
