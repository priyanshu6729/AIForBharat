from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.core.config import settings
import boto3
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
def health():
    """Basic health check"""
    return {"status": "ok", "environment": settings.env}

@router.get("/health/detailed")
def health_detailed(db: Session = Depends(get_db)):
    """Detailed health check with dependency validation"""
    checks = {
        "status": "healthy",
        "checks": {},
        "mentor_models": {
            "routing_order": settings.parsed_mentor_model_order,
            "bedrock_models": settings.parsed_mentor_bedrock_models,
            "stream_fallback_enabled": settings.mentor_stream_fallback_enabled,
            "local_chat_fallback_mode": settings.mentor_local_chat_fallback_mode,
        },
    }
    
    # Database check
    try:
        db.execute(text("SELECT 1"))
        checks["checks"]["database"] = "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        checks["checks"]["database"] = f"error: {str(e)}"
        checks["status"] = "unhealthy"
    
    # AWS S3 check
    try:
        s3 = boto3.client('s3', region_name=settings.aws_region)
        s3.head_bucket(Bucket=settings.s3_bucket)
        checks["checks"]["s3"] = "ok"
    except Exception as e:
        logger.error(f"S3 health check failed: {e}")
        checks["checks"]["s3"] = f"error: {str(e)}"
        checks["status"] = "degraded"
    
    # Bedrock check
    try:
        bedrock = boto3.client('bedrock-runtime', region_name=settings.bedrock_region)
        # Just check if we can create client
        checks["checks"]["bedrock"] = "ok"
    except Exception as e:
        logger.error(f"Bedrock health check failed: {e}")
        checks["checks"]["bedrock"] = f"error: {str(e)}"
        checks["status"] = "degraded"
    
    # AWS credentials + Bedrock check
    try:
        sts = boto3.client("sts", region_name=settings.aws_region)
        identity = sts.get_caller_identity()
        checks["checks"]["aws_credentials"] = "ok"
        checks["checks"]["aws_account"] = identity.get("Account", "unknown")
        checks["checks"]["bedrock"] = "ok"
    except Exception as e:
        logger.error(f"AWS credentials check failed: {e}")
        checks["checks"]["aws_credentials"] = f"error: {str(e)}"
        checks["checks"]["bedrock"] = "degraded - invalid credentials"
        checks["status"] = "degraded"
    
    if checks["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=checks)
    
    return checks

@router.get("/health/ready")
def health_ready(db: Session = Depends(get_db)):
    """Kubernetes-style readiness probe"""
    try:
        db.execute(text("SELECT 1"))
        return {"ready": True}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail={"ready": False, "error": str(e)})

@router.get("/health/live")
def health_live():
    """Kubernetes-style liveness probe"""
    return {"alive": True}
