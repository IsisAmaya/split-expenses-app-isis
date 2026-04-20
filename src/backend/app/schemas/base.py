"""Configuración base para todos los schemas Pydantic."""

from pydantic import BaseModel, ConfigDict


class AppSchema(BaseModel):
    """Schema base con configuración compartida."""

    model_config = ConfigDict(from_attributes=True)
