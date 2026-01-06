"""Main FastAPI application."""
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from graphsql.config import settings
from graphsql.database import db_manager
from graphsql.rest_routes import router as rest_router
from graphsql.graphql_schema import create_graphql_schema


# Configure loguru sink to mirror the requested log level early at import time.
logger.remove()
logger.add(sys.stderr, level=settings.log_level.upper(), enqueue=True, backtrace=True, diagnose=False)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Emit startup and shutdown logs for the application.

    Args:
        app: The running FastAPI application.

    Yields:
        Control back to FastAPI once startup tasks complete.
    """
    # Startup
    logger.info("Starting Auto API...")
    logger.info(f"Database: {settings.database_url.split('@')[-1]}")  # Hide credentials
    logger.info(f"Found {len(db_manager.list_tables())} tables")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Auto API...")


# Create FastAPI app
app = FastAPI(
    title="GraphSQL",
    description="Automatic REST and GraphQL API for any database",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root() -> JSONResponse:
    """Return basic API metadata and discovered tables.

    Returns:
        JSON payload describing available endpoints and table names.

    Examples:
        >>> resp = await root()  # doctest: +SKIP
        >>> resp.body  # doctest: +SKIP
        b'{"name": "Auto API", ...}'
    """
    return JSONResponse({
        "name": "Auto API",
        "version": "0.1.0",
        "endpoints": {
            "rest": "/api",
            "graphql": "/graphql",
            "docs": "/docs",
            "tables": "/api/tables"
        },
        "tables": db_manager.list_tables()
    })


@app.get("/health", tags=["Health"])
async def health_check() -> JSONResponse:
    """Perform a lightweight database connectivity check.

    Returns:
        JSON health status payload; reports 503 on failure.

    Examples:
        >>> await health_check()  # doctest: +SKIP
        <JSONResponse status_code=200>
    """
    try:
        # Test database connection
        tables = db_manager.list_tables()
        return JSONResponse({
            "status": "healthy",
            "database": "connected",
            "tables_count": len(tables)
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


# Include REST routes
app.include_router(rest_router)

# Include GraphQL routes
try:
    graphql_router = create_graphql_schema()
    app.include_router(graphql_router, prefix="", tags=["GraphQL"])
    logger.info("GraphQL endpoint created at /graphql")
except Exception as e:
    logger.error(f"Could not create GraphQL schema: {e}")


def run() -> None:
    """Run the ASGI server with the configured settings."""
    import uvicorn
    
    uvicorn.run(
        "auto_api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()
