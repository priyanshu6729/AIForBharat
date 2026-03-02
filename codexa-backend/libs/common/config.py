from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        protected_namespaces=('settings_',)
    )
    
    env: str = "local"
    log_level: str = "INFO"

    database_url: str

    s3_bucket: str
    s3_prefix: str = "prototype"
    aws_region: str = "us-east-1"

    sqs_queue_url: str | None = None

    bedrock_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    titan_embedding_model_id: str = "amazon.titan-embed-text-v1"

    default_teaching_mode: str = "explanation"

    # Lambda
    lambda_function_name: str = "codexa-analysis"
    lambda_mode: str = "local"
    
    # Cognito
    cognito_user_pool_id: str = ""
    cognito_client_id: str = ""
    cognito_region: str = "us-east-1"
    
    # Local Model
    llm_model_path: str = "models/tinyllama.gguf"
    llm_model_threads: int = 2


settings = Settings()
