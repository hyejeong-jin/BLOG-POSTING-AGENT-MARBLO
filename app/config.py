"""
Environment configuration and settings management for Marblo application.

This module loads configuration from environment variables and provides
a centralized settings object for the entire application.
"""

import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Attributes follow 12-factor app principles for cloud-native deployment.
    """
    
    # Application
    app_name: str = "Marblo"
    app_version: str = "0.1.0"
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = environment == "development"
    
    # API Configuration
    api_title: str = "Marblo API"
    api_version: str = "v1"
    api_prefix: str = "/api/v1"
    
    # Security
    secret_key: str = os.getenv(
        "SECRET_KEY",
        "dev-secret-key-change-in-production"
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours
    refresh_token_expire_days: int = 30
    
    # Password Requirements
    password_min_length: int = 12
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/marblo"
    )
    database_pool_size: int = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    database_max_overflow: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
    database_pool_recycle: int = 3600  # 1 hour
    database_echo: bool = debug
    
    # Redis
    redis_url: str = os.getenv(
        "REDIS_URL",
        "redis://localhost:6379/0"
    )
    redis_cache_ttl: int = 3600  # 1 hour
    
    # AWS Configuration
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    aws_access_key_id: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_s3_bucket: str = os.getenv("AWS_S3_BUCKET", "marblo-photos")
    aws_s3_region: str = os.getenv("AWS_S3_REGION", "us-east-1")
    aws_cloudwatch_log_group: str = os.getenv(
        "AWS_CLOUDWATCH_LOG_GROUP",
        "/marblo/application"
    )
    
    # AI Services
    claude_api_key: Optional[str] = os.getenv("CLAUDE_API_KEY")
    claude_model: str = os.getenv("CLAUDE_MODEL", "claude-3-sonnet-20240229")
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # AI Services (Bedrock)
    use_bedrock: bool = os.getenv("USE_BEDROCK", "true").lower() == "true"
    bedrock_model_id: str = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
    bedrock_max_tokens: int = int(os.getenv("BEDROCK_MAX_TOKENS", "2048"))
    bedrock_region: str = os.getenv("BEDROCK_REGION", os.getenv("AWS_REGION", "us-east-1"))
    
    # Email Service
    email_provider: str = os.getenv("EMAIL_PROVIDER", "ses")  # ses or sendgrid
    sendgrid_api_key: Optional[str] = os.getenv("SENDGRID_API_KEY")
    email_from: str = os.getenv("EMAIL_FROM", "noreply@marblo.com")
    email_from_name: str = os.getenv("EMAIL_FROM_NAME", "Marblo")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # CORS
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]
    if environment == "production":
        cors_origins = [
            "https://marblo.com",
            "https://www.marblo.com",
        ]
    
    cors_credentials: bool = True
    cors_methods: list[str] = ["*"]
    cors_headers: list[str] = ["*"]
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO" if environment == "production" else "DEBUG")
    log_format: str = "json"  # json or text
    
    # File Upload
    max_file_size_mb: int = 50  # Maximum file size for photos
    max_file_size_style_mb: int = 100  # Maximum file size for style learning
    allowed_image_types: list[str] = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    
    # Generation
    generation_timeout_seconds: int = 60
    photo_analysis_timeout_seconds: int = 30
    
    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra env vars not defined in Settings


# Global settings instance
settings = Settings()


