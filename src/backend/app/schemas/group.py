"""Schemas de grupos y miembros."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from .base import AppSchema


class MemberResponse(AppSchema):
    """Respuesta de un miembro del grupo."""

    id: UUID
    name: str


class GroupCreate(AppSchema):
    """Request para crear un grupo."""

    name: str = Field(
        ..., min_length=1, max_length=100, examples=["Viaje a Santa Marta"]
    )
    members: list[str] = Field(
        ..., min_length=2, examples=[["Samuel", "Isis", "Santiago"]]
    )


class GroupListItem(AppSchema):
    """Grupo resumido para listados."""

    id: UUID
    name: str
    member_count: int
    created_at: datetime


class GroupResponse(AppSchema):
    """Respuesta completa de un grupo."""

    id: UUID
    name: str
    members: list[MemberResponse]
    expense_count: int
    created_at: datetime
