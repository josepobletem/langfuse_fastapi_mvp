"""
Configuration module for the FastAPI + Langfuse application.

This module follows the 12-factor principle: all configuration is sourced
from environment variables. It uses Pydantic's BaseModel to provide
validation and default values.

Environment variables:
    APP_ENV              : Current environment (default: "dev")
    LOG_LEVEL            : Logging level (default: "INFO")
    PORT                 : App port (default: 8000)
    OPENAI_API_KEY       : Optional API key for OpenAI client
    LANGFUSE_PUBLIC_KEY  : Optional Langfuse public key
    LANGFUSE_SECRET_KEY  : Optional Langfuse secret key
    LANGFUSE_HOST        : Optional Langfuse host URL
"""

import os

from pydantic import BaseModel


class Settings(BaseModel):
    """Application settings parsed from environment variables.

    Attributes:
        app_env: Current environment string ("dev", "staging", "prod", etc.)
        log_level: Logging verbosity (e.g., "DEBUG", "INFO", "WARNING").
        port: Port the application should listen on.
        openai_api_key: OpenAI API key (optional, can be None in tests).
        langfuse_public_key: Langfuse public key (optional).
        langfuse_secret_key: Langfuse secret key (optional).
        langfuse_host: Langfuse host URL (optional).
    """

    app_env: str = os.getenv("APP_ENV", "dev")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    port: int = int(os.getenv("PORT", "8000"))
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    langfuse_public_key: str | None = os.getenv("LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str | None = os.getenv("LANGFUSE_SECRET_KEY")
    langfuse_host: str | None = os.getenv("LANGFUSE_HOST")


# Global settings instance used throughout the app
settings = Settings()
