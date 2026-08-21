"""
Logging configuration for Marblo application.

Sets up structured logging with structlog and CloudWatch integration
for production environments.
"""

import json
import logging
import sys
from typing import Any

import structlog
import watchtower

from app.config import settings


def setup_logging() -> None:
    """
    Configure structured logging with appropriate handlers.
    
    - Development: logs to console with pretty formatting
    - Production: logs to CloudWatch with JSON formatting
    """
    
    # Shared structlog configuration
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
            if settings.log_format == "json"
            else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler (for development and as fallback)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.log_level)
    
    # Format for console output
    console_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # CloudWatch handler (for production)
    if settings.environment == "production":
        try:
            cloudwatch_handler = watchtower.CloudWatchLogHandler(
                log_group=settings.aws_cloudwatch_log_group,
                stream_name=settings.app_name,
                region_name=settings.aws_region,
            )
            cloudwatch_handler.setLevel(settings.log_level)
            
            # JSON formatter for CloudWatch
            json_formatter = logging.Formatter(
                json.dumps({
                    "timestamp": "%(asctime)s",
                    "level": "%(levelname)s",
                    "logger": "%(name)s",
                    "message": "%(message)s",
                    "module": "%(module)s",
                })
            )
            cloudwatch_handler.setFormatter(json_formatter)
            root_logger.addHandler(cloudwatch_handler)
        except Exception as e:
            root_logger.warning(
                f"Failed to configure CloudWatch logging: {e}. "
                "Falling back to console logging."
            )


def get_logger(name: str) -> Any:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name, typically __name__ of the calling module
        
    Returns:
        A structlog logger instance
    """
    return structlog.get_logger(name)


