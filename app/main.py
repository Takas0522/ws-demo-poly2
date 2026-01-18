"""User Management Service - Main Application"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys

from app.config import settings
from app.utils import cosmos_client
from app.routers import user_router, health_router, tenant_router
from app.middleware import validate_tenant_id

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting User Management Service...")
    try:
        cosmos_client.initialize()
        logger.info("CosmosDB initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize CosmosDB: {str(e)}")
        logger.warning(
            "Service will start without CosmosDB connection. Some endpoints may not work.")

    yield

    # Shutdown
    logger.info("Shutting down User Management Service...")
    try:
        cosmos_client.close()
    except Exception as e:
        logger.error(f"Error closing CosmosDB connection: {str(e)}")


# Create FastAPI application
app = FastAPI(
    title="User Management Service",
    description="User Management Service with CRUD operations and tenant isolation",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add tenant validation middleware
app.middleware("http")(validate_tenant_id)

# Exception handlers


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred"
            }
        }
    )


# Include routers
app.include_router(health_router)
app.include_router(user_router)
app.include_router(tenant_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development"
    )
