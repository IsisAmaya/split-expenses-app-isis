"""Tests unitarios para balances y liquidaciones."""

from decimal import Decimal
from uuid import uuid4

import pytest

from app.services import balance_service, expense_service


def test_calculate_balances_returns_expected_net_amounts(db_session, sample_group):
    """Verifica el balance neto final de cada miembro tras varios gastos."""
    ana, beto, _ = sample_group.members

    expense_service.create_expense(
        db=db_session,
        group_id=sample_group.id,
        paid_by_id=ana.id,
        description="Almuerzo",
        amount=Decimal("60.00"),
    )
    expense_service.create_expense(
        db=db_session,
        group_id=sample_group.id,
        paid_by_id=beto.id,
        description="Taxi",
        amount=Decimal("30.00"),
        split_among_ids=[ana.id, beto.id],
    )

    balances = balance_service.calculate_balances(db_session, sample_group.id)

    assert balances == {
        "Ana": Decimal("25.00"),
        "Beto": Decimal("-5.00"),
        "Carla": Decimal("-20.00"),
    }


def test_calculate_balances_rejects_unknown_group(db_session):
    """Comprueba que calcular balances falle si el grupo no existe."""
    with pytest.raises(ValueError, match="El grupo no existe"):
        balance_service.calculate_balances(db_session, uuid4())


def test_calculate_settlements_returns_minimum_transfers(db_session, sample_group):
    """Valida que las transferencias sugeridas minimicen el número de pagos."""
    ana, _, _ = sample_group.members

    expense_service.create_expense(
        db=db_session,
        group_id=sample_group.id,
        paid_by_id=ana.id,
        description="Hospedaje",
        amount=Decimal("90.00"),
    )

    settlements = balance_service.calculate_settlements(db_session, sample_group.id)

    assert settlements == [
        {"from": "Beto", "to": "Ana", "amount": Decimal("30.00")},
        {"from": "Carla", "to": "Ana", "amount": Decimal("30.00")},
    ]


def test_calculate_settlements_returns_empty_list_when_everything_is_settled(
    db_session, sample_group
):
    """Asegura que no se propongan pagos cuando no hay deudas pendientes."""
    settlements = balance_service.calculate_settlements(db_session, sample_group.id)

    assert not settlements
