"""Configuración de la aplicación desde variables de entorno."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings de la aplicación, cargados desde variables de entorno."""

    database_url: str = "postgresql://splitwise:splitwise@localhost:5432/splitwise"
    app_env: str = "development"
    port: int = 8000
    app_name: str = "Split de Gastos API"
    app_version: str = "1.0.0"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
