"""
FastAPI application factory and middleware setup for Marblo.

This module initializes the FastAPI application with all necessary
middleware, error handlers, and event handlers for the Marblo service.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.logging_config import get_logger, setup_logging
from app.routers import auth

# Initialize logger
logger = get_logger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Manage application startup and shutdown events.
    
    Args:
        app: FastAPI application instance
        
    Yields:
        Control flow through the application lifecycle
    """
    # Startup
    logger.info(
        "Application startup",
        app_name=settings.app_name,
        environment=settings.environment,
        version=settings.app_version,
    )
    
    yield
    
    # Shutdown
    logger.info("Application shutdown")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Sets up:
    - CORS middleware for cross-origin requests
    - Security headers middleware
    - Compression middleware for responses
    - Rate limiting middleware
    - Structured logging
    - Error handlers
    
    Returns:
        Configured FastAPI application instance
    """
    
    # Setup logging first
    setup_logging()
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.api_title,
        description="AI-powered blog post generation service for information-delivery bloggers",
        version=settings.api_version,
        lifespan=lifespan,
    )
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"] if settings.debug else ["marblo.com", "www.marblo.com"],
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_credentials,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )
    
    # Compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Rate limiting
    if settings.rate_limit_enabled:
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
    
    # Security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        """Add security headers to all responses."""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # HSTS for production
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # CSP
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self';"
        )
        
        return response
    
    # Logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log incoming requests and responses."""
        logger.info(
            "Incoming request",
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else "unknown",
        )
        
        response = await call_next(request)
        
        logger.info(
            "Response sent",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
        )
        
        return response
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """
        Health check endpoint for load balancers and monitoring.
        
        Returns:
            Health status
        """
        return {
            "status": "healthy",
            "app": settings.app_name,
            "environment": settings.environment,
            "version": settings.app_version,
        }
    
    # Register routers
    from app.routers import photos, styles, posts, export, history, users, marblo
    app.include_router(auth.router, prefix=settings.api_prefix)
    app.include_router(photos.router, prefix=settings.api_prefix)
    app.include_router(styles.router, prefix=settings.api_prefix)
    app.include_router(posts.router, prefix=settings.api_prefix)
    app.include_router(export.router, prefix=settings.api_prefix)
    app.include_router(history.router, prefix=settings.api_prefix)
    app.include_router(users.router, prefix=settings.api_prefix)
    app.include_router(marblo.router, prefix=settings.api_prefix)
    
    # Root endpoint
    @app.get("/")
    async def root():
        """
        Root endpoint providing API information.
        
        Returns:
            API information
        """
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "api_prefix": settings.api_prefix,
            "environment": settings.environment,
            "documentation": "/docs",
        }
    
    # Mount static files for frontend
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        
        # Serve index.html for root path if static exists
        @app.get("/app")
        async def serve_app():
            """Serve the web app."""
            from fastapi.responses import FileResponse
            return FileResponse(str(static_dir / "index.html"))
    
    # Global exception handler for validation errors
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions globally."""
        logger.error(
            "Unhandled exception",
            path=request.url.path,
            error=str(exc),
            error_type=type(exc).__name__,
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(exc) if settings.debug else "An error occurred",
            },
        )
    
    logger.info("FastAPI application created successfully")
    
    return app


async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors."""
    logger.warning(
        "Rate limit exceeded",
        path=request.url.path,
        client=request.client.host if request.client else "unknown",
    )
    
    return JSONResponse(
        status_code=429,
        content={"error": "Rate limit exceeded", "detail": str(exc)},
    )


# Create application instance
app = create_app()


