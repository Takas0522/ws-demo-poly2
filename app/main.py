"""
Main FastAPI application for User Management Service.
"""
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db import db_client
from app.services import auth_client
from app.api import health, tenants


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Lifespan context manager for startup and shutdown events.
    
    Args:
        app: FastAPI application instance.
    
    Yields:
        None
    """
    # Startup
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Environment: {settings.environment}")
    
    # Connect to Cosmos DB
    try:
        db_client.connect()
        print("✓ Connected to Cosmos DB")
    except Exception as e:
        print(f"⚠ Warning: Could not connect to Cosmos DB: {e}")
    
    # Initialize Auth Service client
    try:
        await auth_client.initialize()
        print("✓ Initialized Auth Service client")
    except Exception as e:
        print(f"⚠ Warning: Could not initialize Auth Service client: {e}")
    
    yield
    
    # Shutdown
    print("Shutting down...")
    
    # Disconnect from Cosmos DB
    db_client.disconnect()
    print("✓ Disconnected from Cosmos DB")
    
    # Close Auth Service client
    await auth_client.close()
    print("✓ Closed Auth Service client")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="User Management Service for managing tenants and tenant-associated users",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods.split(",") if settings.cors_allow_methods != "*" else ["*"],
    allow_headers=settings.cors_allow_headers.split(",") if settings.cors_allow_headers != "*" else ["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(tenants.router)


@app.get("/", tags=["root"])
async def root() -> dict:
    """
    Root endpoint.
    
    Returns:
        Dict with service information.
    """
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
    )
