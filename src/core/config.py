from pydantic_settings import BaseSettings, SettingsConfigDict

from .logging_config import setup_logging


class AppConfig(BaseSettings):
    """Application configuration loaded from environment variables."""

    service_name: str = "generated-service"
    service_version: str = "1.0.0"
    service_port: int = 8000
    service_host: str = "0.0.0.0"

    redis_url: str = "redis://localhost:6379"
    redis_stream_name: str = "tasks:stream"
    redis_consumer_group: str = "processors"
    redis_consumer_name: str = "worker"

    statsd_host: str = "localhost"
    statsd_port: int = 8125
    statsd_prefix: str = "microservice"

    jaeger_endpoint: str = "http://localhost:14268/api/traces"
    jaeger_service_name: str = "generated-service"

    loki_endpoint: str = "http://localhost:3100/loki/api/v1/push"

    uvloop_enabled: bool = True
    worker_processes: str = "auto"
    max_concurrent_tasks: int = 1000
    task_timeout: int = 30
    max_payload_size: int = 1048576

    shutdown_timeout: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


def configure_logging() -> None:
    """Configure application logging."""

    setup_logging()


def get_config() -> AppConfig:
    """Return the application configuration instance."""
    return AppConfig()
