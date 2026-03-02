from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field, AliasChoices, field_validator
import secrets


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        protected_namespaces=('settings_',),
        extra="ignore",
    )
    
    env: str = "local"
    log_level: str = "INFO"
    frontend_url: str = "http://localhost:3000"
    secret_key: str = "dev-secret-key-change-in-production"
    allowed_hosts: str = "localhost,127.0.0.1"
    
    # Rate limiting
    rate_limit_per_minute: int = 100
    rate_limit_per_hour: int = 2000
    
    # Monitoring
    sentry_dsn: str | None = None
    
    database_url: str
    s3_bucket: str
    s3_prefix: str = "prototype"
    aws_region: str = Field(
        default="us-east-1",
        validation_alias=AliasChoices("AWS_REGION", "AWS_DEFAULT_REGION"),
    )
    sqs_queue_url: str | None = None
    bedrock_region: str = Field(default="us-east-1", validation_alias=AliasChoices("BEDROCK_REGION", "AWS_REGION"))
    nova_model_id: str = Field(
        default="amazon.nova-lite-v1",
        validation_alias=AliasChoices("NOVA_MODEL_ID", "BEDROCK_MODEL_ID"),
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
    
    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Ensure secret key is changed in production"""
        if info.data.get("env") == "production" and "change-in-production" in v.lower():
            raise ValueError("SECRET_KEY must be changed for production deployment!")
        if info.data.get("env") == "production" and len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters in production")
        return v
    
    @field_validator("frontend_url")
    @classmethod
    def validate_frontend_url(cls, v: str, info) -> str:
        """Ensure frontend URL is HTTPS in production"""
        if info.data.get("env") == "production" and not v.startswith("https://"):
            raise ValueError("FRONTEND_URL must use HTTPS in production")
        return v
    
    @property
    def is_production(self) -> bool:
        return self.env == "production"
    
    @property
    def allowed_origins(self) -> list[str]:
        """Get CORS allowed origins"""
        if self.env == "local":
            return ["*"]
        return [self.frontend_url] + [
            f"https://{host}" for host in self.allowed_hosts.split(",")
        ]


settings = Settings()
