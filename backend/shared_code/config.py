"""
Configuration module - reads environment variables and constructs connection strings.
Supports both local development and Azure production environments.
"""
import os
from functools import lru_cache
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    host: str
    port: int
    name: str
    user: str
    password: str
    sslmode: str

    @property
    def url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}?sslmode={self.sslmode}"
        )

    @property
    def async_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )


@dataclass
class AzureOpenAIConfig:
    endpoint: str
    api_key: str
    deployment: str
    api_version: str = "2024-02-01"

    @property
    def is_configured(self) -> bool:
        return bool(self.endpoint and self.api_key and self.deployment)


@dataclass
class AppConfig:
    db: DatabaseConfig
    openai: AzureOpenAIConfig
    app_insights_connection_string: str
    environment: str


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    return AppConfig(
        db=DatabaseConfig(
            host=os.environ.get("DB_HOST", "localhost"),
            port=int(os.environ.get("DB_PORT", "5432")),
            name=os.environ.get("DB_NAME", "financedb"),
            user=os.environ.get("DB_USER", "postgres"),
            password=os.environ.get("DB_PASSWORD", "postgres"),
            sslmode=os.environ.get("DB_SSLMODE", "disable"),
        ),
        openai=AzureOpenAIConfig(
            endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
            api_key=os.environ.get("AZURE_OPENAI_API_KEY", ""),
            deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT", ""),
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-01"),
        ),
        app_insights_connection_string=os.environ.get(
            "APPLICATIONINSIGHTS_CONNECTION_STRING", ""
        ),
        environment=os.environ.get("ENVIRONMENT", "local"),
    )
