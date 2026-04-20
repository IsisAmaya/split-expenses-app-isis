"""Schema del health check."""

from .base import AppSchema


class HealthResponse(AppSchema):
    """Respuesta del health check."""

    status: str
    database: str
    environment: str
    version: str
