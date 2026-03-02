#!/usr/bin/env python3
# filepath: /Users/priyanshuraj/Documents/New project/codexa/codexa-backend/scripts/check_production.py
"""
Production Readiness Checker for Codexa Backend
Run this before deploying to production
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
import boto3
from sqlalchemy import create_engine, text

def check_env_vars():
    """Check critical environment variables"""
    print("\n🔍 Checking Environment Variables")
    print("-" * 50)
    
    checks = []
    
    # Check ENV
    if settings.env != "production":
        checks.append(("❌", f"ENV is '{settings.env}', should be 'production'"))
    else:
        checks.append(("✓", "ENV is set to production"))
    
    # Check SECRET_KEY
    if "change-in-production" in settings.secret_key.lower():
        checks.append(("❌", "SECRET_KEY must be changed!"))
    elif len(settings.secret_key) < 32:
        checks.append(("❌", f"SECRET_KEY too short ({len(settings.secret_key)} chars, need 32+)"))
    else:
        checks.append(("✓", "SECRET_KEY is properly configured"))
    
    # Check HTTPS
    if not settings.frontend_url.startswith("https://"):
        checks.append(("❌", f"FRONTEND_URL should use HTTPS: {settings.frontend_url}"))
    else:
        checks.append(("✓", "FRONTEND_URL uses HTTPS"))
    
    # Check Lambda mode
    if settings.lambda_mode == "local":
        checks.append(("⚠", "LAMBDA_MODE is 'local', should be 'invoke' in production"))
    else:
        checks.append(("✓", "LAMBDA_MODE is set to invoke"))
    
    for icon, msg in checks:
        print(f"{icon} {msg}")
    
    return all(icon == "✓" for icon, _ in checks)

def check_database():
    """Check database connectivity"""
    print("\n🗄️  Checking Database")
    print("-" * 50)
    
    try:
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✓ Database connected: {version[:50]}...")
            
            # Check for required tables
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            ))
            tables = [row[0] for row in result]
            if tables:
                print(f"✓ Found {len(tables)} tables")
            else:
                print("⚠ No tables found - run migrations?")
        
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_aws():
    """Check AWS credentials and services"""
    print("\n☁️  Checking AWS Services")
    print("-" * 50)
    
    checks = []
    
    # Check credentials
    try:
        sts = boto3.client('sts', region_name=settings.aws_region)
        identity = sts.get_caller_identity()
        print(f"✓ AWS credentials valid")
        print(f"  Account: {identity['Account']}")
        print(f"  ARN: {identity['Arn']}")
        checks.append(True)
    except Exception as e:
        print(f"❌ AWS credentials error: {e}")
        checks.append(False)
    
    # Check S3 bucket
    try:
        s3 = boto3.client('s3', region_name=settings.aws_region)
        s3.head_bucket(Bucket=settings.s3_bucket)
        print(f"✓ S3 bucket '{settings.s3_bucket}' accessible")
        checks.append(True)
    except Exception as e:
        print(f"❌ S3 bucket error: {e}")
        checks.append(False)
    
    # Check Lambda function
    try:
        lambda_client = boto3.client('lambda', region_name=settings.aws_region)
        response = lambda_client.get_function(FunctionName=settings.lambda_function_name)
        print(f"✓ Lambda function '{settings.lambda_function_name}' exists")
        checks.append(True)
    except Exception as e:
        print(f"❌ Lambda function error: {e}")
        checks.append(False)
    
    # Check Bedrock
    try:
        bedrock = boto3.client('bedrock-runtime', region_name=settings.bedrock_region)
        print(f"✓ Bedrock client created in {settings.bedrock_region}")
        checks.append(True)
    except Exception as e:
        print(f"❌ Bedrock error: {e}")
        checks.append(False)
    
    return all(checks)

def check_cognito():
    """Check Cognito configuration"""
    print("\n🔐 Checking Cognito")
    print("-" * 50)
    
    if not settings.cognito_user_pool_id:
        print("⚠ Cognito User Pool ID not set")
        return False
    
    if not settings.cognito_client_id:
        print("⚠ Cognito Client ID not set")
        return False
    
    try:
        cognito = boto3.client('cognito-idp', region_name=settings.cognito_region)
        response = cognito.describe_user_pool(UserPoolId=settings.cognito_user_pool_id)
        print(f"✓ User Pool exists: {response['UserPool']['Name']}")
        return True
    except Exception as e:
        print(f"❌ Cognito error: {e}")
        return False

def main():
    print("=" * 50)
    print("🚀 Codexa Production Readiness Check")
    print("=" * 50)
    
    results = {
        "Environment Variables": check_env_vars(),
        "Database": check_database(),
        "AWS Services": check_aws(),
        "Cognito": check_cognito(),
    }
    
    print("\n" + "=" * 50)
    print("📊 Summary")
    print("=" * 50)
    
    for check, passed in results.items():
        icon = "✅" if passed else "❌"
        print(f"{icon} {check}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✅ All checks passed! Ready for production deployment.")
        sys.exit(0)
    else:
        print("\n❌ Some checks failed. Fix issues before deploying.")
        sys.exit(1)

if __name__ == "__main__":
    main()