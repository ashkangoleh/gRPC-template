"""
Settings module for the server
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# Define the Settings class


class Settings(BaseSettings):
    # For ClickHouse connection
    CLICKHOUSE_HOST: str
    CLICKHOUSE_PORT: int
    CLICKHOUSE_USER: str
    CLICKHOUSE_PASSWORD: str
    CLICKHOUSE_DATABASE: str
    # For gRPC server connection
    GRPC_SERVER_HOST: str
    GRPC_SERVER_PORT: int
    # For gRPC protocol
    SERVICE_NAME: str
    REQUESTS_TOTAL_DESCRIPTION: str
    OTEL_EXPORTER_OTLP_TRACES_ENDPOINT:str
    OTEL_EXPORTER_OTLP_TRACES_PROTOCOL:str
    OTEL_EXPORTER_OTLP_METRICS_ENDPOINT:str
    OTEL_EXPORTER_OTLP_METRICS_PROTOCOL:str
    OTEL_EXPORTER_OTLP_ENDPOINT:str
    OTEL_EXPORTER_OTLP_PROTOCOL:str
     # Define the model_config property for environment variables
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8')

# Define the cached_setting function and cache the result
@lru_cache
def cached_setting():
    """
    Returns a cached instance of the Settings class.

    This function is decorated with @lru_cache to ensure that only one instance
    of the Settings class is created and reused. This is useful to avoid loading
    the environment variables and configuration files multiple times.

    Returns:
        Settings: An instance of the Settings class.
    """
    return Settings()

settings: Settings = cached_setting()
