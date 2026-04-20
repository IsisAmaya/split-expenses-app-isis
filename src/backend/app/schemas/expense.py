"""Schemas de gastos."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from .base import AppSchema


class ExpenseSplitResponse(AppSchema):
    """Detalle de cómo se dividió un gasto."""

    member_name: str
    amount: Decimal


class ExpenseCreate(AppSchema):
    """Request para crear un gasto."""

    description: str = Field(
        ..., min_length=1, max_length=200, examples=["Hotel en Santa Marta"]
    )
    amount: Decimal = Field(..., gt=0, examples=[400000])
    paid_by_id: UUID
    split_among_ids: list[UUID] | None = Field(
        default=None,
        description="IDs de miembros entre quienes se divide. Si es null, se divide entre todos.",
    )


class ExpenseResponse(AppSchema):
    """Respuesta de un gasto registrado."""

    id: UUID
    description: str
    amount: Decimal
    paid_by: str
    splits: list[ExpenseSplitResponse]
    created_at: datetime
