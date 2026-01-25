# Scripts

This directory contains utility scripts for setting up and managing the User Management Service.

## Setup Scripts

### setup_cosmos_containers.py

Creates Cosmos DB containers with proper partition keys.

**Usage:**
```bash
python scripts/setup_cosmos_containers.py
```

**What it does:**
- Creates `tenants` container with partition key `/id`
- Creates `tenant-users` container with partition key `/tenantId`
- Sets throughput to 400 RU/s for each container

**Prerequisites:**
- Cosmos DB database `management-app` must exist
- Environment variables must be configured (see `.env.example`)

### seed_data.py

Creates initial seed data for the User Management Service.

**Usage:**
```bash
python scripts/seed_data.py
```

**What it does:**
- Creates a privileged tenant (`tenant-001`: "特権管理テナント")
- Creates an initial user binding (maps `user-001` to `tenant-001`)

**Prerequisites:**
- Cosmos DB containers must be created (run `setup_cosmos_containers.py` first)
- User `user-001` should exist in the Auth Service

## Typical Setup Workflow

1. Ensure Cosmos DB database exists
2. Run container setup:
   ```bash
   python scripts/setup_cosmos_containers.py
   ```
3. Run seed data:
   ```bash
   python scripts/seed_data.py
   ```
4. Verify setup by starting the service:
   ```bash
   python -m uvicorn app.main:app --reload
   ```
