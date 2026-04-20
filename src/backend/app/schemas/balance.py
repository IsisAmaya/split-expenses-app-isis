"""Schemas de balances y transferencias."""

from decimal import Decimal

from .base import AppSchema


class BalanceResponse(AppSchema):
    """Balance de un miembro del grupo."""

    member: str
    balance: Decimal


class SettlementResponse(AppSchema):
    """Transferencia sugerida para saldar deudas."""

    from_member: str
    to_member: str
    amount: Decimal
