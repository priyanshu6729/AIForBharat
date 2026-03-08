from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field, AliasChoices, field_validator
import secrets
import os


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        protected_namespaces=('settings_',),
        extra="ignore",
    )
    
    env: str = Field(default="development", validation_alias=AliasChoices("ENV", "ENVIRONMENT"))
    log_level: str = "INFO"
    frontend_url: str = "http://localhost:3000"
    secret_key: str = "dev-secret-key-change-in-production"
    allowed_hosts: str = "localhost,127.0.0.1"
    
    # Railway-specific
    railway_environment: str | None = Field(default=None, validation_alias="RAILWAY_ENVIRONMENT")
    railway_service_name: str | None = Field(default=None, validation_alias="RAILWAY_SERVICE_NAME")
    port: int = Field(default=8000, validation_alias="PORT")
    
    # Rate limiting
    rate_limit_per_minute: int = 100
    rate_limit_per_hour: int = 2000
    
    # Monitoring
    sentry_dsn: str | None = None
    
    # Database - Railway provides DATABASE_URL
    database_url: str = Field(
        default="postgresql://localhost/codexa",  # Temporary default for validation
        validation_alias=AliasChoices("DATABASE_URL", "DATABASE_PRIVATE_URL")
    )
    
    s3_bucket: str = Field(default="")  # Make optional temporarily
    s3_prefix: str = "prototype"
    aws_region: str = Field(
        default="us-east-1",
        validation_alias=AliasChoices("AWS_REGION", "AWS_DEFAULT_REGION"),
    )
    sqs_queue_url: str | None = None
    bedrock_region: str = Field(default="us-east-1", validation_alias=AliasChoices("BEDROCK_REGION", "AWS_REGION"))
    nova_model_id: str = Field(
        default="amazon.nova-micro-v1:0",  # ✅ Valid model ID with version
        validation_alias=AliasChoices("NOVA_MODEL_ID", "BEDROCK_MODEL_ID"),
    )
    mentor_model_order: str = Field(
        default="bedrock,local",
        validation_alias=AliasChoices("MENTOR_MODEL_ORDER"),
    )
    mentor_bedrock_models: str = Field(
        default="",
        validation_alias=AliasChoices("MENTOR_BEDROCK_MODELS"),
    )
    mentor_stream_fallback_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("MENTOR_STREAM_FALLBACK_ENABLED"),
    )
    mentor_local_chat_fallback_mode: str = Field(
        default="heuristic",
        validation_alias=AliasChoices("MENTOR_LOCAL_CHAT_FALLBACK_MODE"),
    )
    titan_embedding_model_id: str = Field(
        default="amazon.titan-embed-text-v1",
        validation_alias=AliasChoices("TITAN_EMBEDDING_MODEL_ID", "TITAN_MODEL_ID"),
    )
    default_teaching_mode: str = "explanation"
    
    # Lambda
    lambda_function_name: str = "codexa-analysis"
    lambda_mode: str = "local"
    
    # Cognito
    cognito_user_pool_id: str = ""
    cognito_client_id: str = ""
    cognito_region: str = "us-east-1"
    
    # Local Model
    llm_model_path: str = Field(
        default="models/tinyllama.gguf",
        validation_alias=AliasChoices("LLM_MODEL_PATH", "MODEL_PATH"),
    )
    llm_model_threads: int = Field(
        default=2,
        validation_alias=AliasChoices("LLM_MODEL_THREADS", "MODEL_THREADS"),
    )
    
    @field_validator("database_url")
    @classmethod
    def fix_railway_database_url(cls, v: str) -> str:
        """Fix Railway's postgres:// to postgresql+psycopg2://"""
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+psycopg2://", 1)
        return v
    
    @field_validator("s3_bucket")
    @classmethod
    def validate_s3_bucket(cls, v: str, info) -> str:
        """Validate S3 bucket in production"""
        env = info.data.get("env", "development")
        if env == "production" and not v:
            raise ValueError(
                "S3_BUCKET is required in production! "
                "Please set it in Railway dashboard under Variables tab."
            )
        return v
    
    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Ensure secret key is changed in production"""
        if info.data.get("env") == "production" and "change-in-production" in v.lower():
            raise ValueError("SECRET_KEY must be changed for production deployment!")
        if info.data.get("env") == "production" and len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters in production")
        return v
    
    @field_validator("env")
    @classmethod
    def detect_railway(cls, v: str, info) -> str:
        """Auto-detect Railway environment"""
        # If RAILWAY_ENVIRONMENT is set, use it
        railway_env = info.data.get("railway_environment")
        if railway_env:
            return "production" if railway_env == "production" else "development"
        return v
    
    @field_validator("frontend_url")
    @classmethod
    def validate_frontend_url(cls, v: str, info) -> str:
        """Ensure frontend URL is HTTPS in production"""
        env = info.data.get("env", "development")
        if env == "production" and not v.startswith(("https://", "http://localhost")):
            if not v.startswith("http://"):
                raise ValueError("FRONTEND_URL must use HTTPS in production")
        return v
    
    @property
    def is_production(self) -> bool:
        return self.env == "production"
    
    @property
    def is_railway(self) -> bool:
        """Check if running on Railway"""
        return self.railway_environment is not None
    
    @property
    def allowed_origins(self) -> list[str]:
        """Get CORS allowed origins"""
        if self.env in ["local", "development"]:
            return ["*"]
        
        origins = [self.frontend_url]
        
        # Add Railway preview URLs
        if self.is_railway:
            origins.append("https://*.railway.app")
        
        # Add configured hosts
        origins.extend([
            f"https://{host}" for host in self.allowed_hosts.split(",")
        ])
        
        return origins

    @property
    def parsed_mentor_model_order(self) -> list[str]:
        values = [value.strip().lower() for value in self.mentor_model_order.split(",") if value.strip()]
        normalized: list[str] = []
        for value in values:
            if value in {"bedrock", "local"} and value not in normalized:
                normalized.append(value)
        return normalized or ["bedrock", "local"]

    @property
    def parsed_mentor_bedrock_models(self) -> list[str]:
        values = [value.strip() for value in self.mentor_bedrock_models.split(",") if value.strip()]
        if values:
            return values
        return [self.nova_model_id] if self.nova_model_id else []

settings = Settings()
