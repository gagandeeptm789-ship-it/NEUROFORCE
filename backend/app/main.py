"""
The Forwarded Seal — Backend Main Application
FastAPI entrypoint, middleware configuration, routers registration, and startup lifecycle.
"""

import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.database import engine, init_db
from app.routers.auth import router as auth_router
from app.routers.notices import router as notices_router

# Configure structured application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("forwarded_seal")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events: startup and shutdown."""
    logger.info("Starting up %s (env: %s)...", settings.PROJECT_NAME, settings.ENVIRONMENT)
    # Initialize database tables
    try:
        init_db()
        logger.info("Database connectivity verified.")
    except Exception as e:
        logger.error("Database initialization error: %s", e)
    yield
    logger.info("Shutting down %s...", settings.PROJECT_NAME)


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Official backend platform for university document authenticity verification.\n\n"
        "### Key Capabilities:\n"
        "- **Administrator Authentication:** Secure bcrypt hashing, JWT issuance & verification.\n"
        "- **Official Notice Creation:** Deep file inspection (magic bytes), metadata storage.\n"
        "- **Institutional Notice ID Generation:** Format `FS-{INSTITUTION}-{YEAR}-{CODE}`.\n"
        "- **Phase 3 Ready:** Extensible schema and service layer prepared for SHA-256 and digital signatures."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ------------------------------------------------------------------------------
# Security: Restricted CORS Middleware
# ------------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# ------------------------------------------------------------------------------
# Global Error Handling (OWASP / Information Leakage Prevention)
# ------------------------------------------------------------------------------
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Ensure internal unhandled exceptions never expose internal stack traces."""
    logger.error("Unhandled exception processing %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact the administrator."},
    )


# ------------------------------------------------------------------------------
# Include Routers
# ------------------------------------------------------------------------------
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(notices_router, prefix=settings.API_V1_PREFIX)


# ------------------------------------------------------------------------------
# System Endpoints
# ------------------------------------------------------------------------------
@app.get("/", tags=["System"])
def root():
    """Welcome and API metadata endpoint."""
    return {
        "project": settings.PROJECT_NAME,
        "version": "2.0.0",
        "phase": "Phase 2 (Admin Auth & Notice Creation)",
        "docs": "/docs",
        "status": "operational",
    }


@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint for container orchestrators and monitoring."""
    db_status = "connected"
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
    except Exception as e:
        logger.error("Healthcheck DB ping failed: %s", e)
        db_status = "disconnected"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "environment": settings.ENVIRONMENT,
    }

