from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.logging import configure_logging
from app.routers import analyze, visualize, guidance, execute, session, health, learn, progress
from app.routes import auth
from app.core.config import settings
from sqlalchemy import text
import logging

configure_logging()
logger = logging.getLogger(__name__)

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"]
)

app = FastAPI(
    title="Codexa Backend",
    version="0.1.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security: Trusted Host Middleware in production
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts.split(",")
    )

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    max_age=3600,
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {exc}",
        exc_info=True,
        extra={
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else "unknown"
        }
    )
    
    # Don't leak error details in production
    if settings.is_production:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"}
        )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)}
    )

# Include routers
app.include_router(analyze.router)
app.include_router(visualize.router)
app.include_router(guidance.router)
app.include_router(execute.router)
app.include_router(session.router)
app.include_router(health.router)
app.include_router(learn.router)
app.include_router(progress.router)
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

@app.on_event("startup")
async def startup_event():
    logger.info(f"Codexa Backend starting up in {settings.env} mode...")
    
    # Validate production configuration
    if settings.is_production:
        logger.info("Running production configuration checks...")
        try:
            # Check database connectivity
            from app.database import SessionLocal
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            logger.info("✓ Database connection successful")
        except Exception as e:
            logger.error(f"✗ Database connection failed: {e}")
            raise
        
        # Check AWS credentials
        try:
            import boto3
            sts = boto3.client('sts', region_name=settings.aws_region)
            sts.get_caller_identity()
            logger.info("✓ AWS credentials valid")
        except Exception as e:
            logger.error(f"✗ AWS credentials check failed: {e}")
            raise
    
    logger.info("Startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Codexa Backend shutting down...")
