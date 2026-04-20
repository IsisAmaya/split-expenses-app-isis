"""Tests unitarios para la lógica de gastos."""

from decimal import Decimal
from uuid import uuid4

import pytest

from app.models import ExpenseSplit
from app.services import expense_service


def test_create_expense_splits_amount_equally_and_adjusts_rounding(
    db_session, sample_group
):
    """Valida el reparto equitativo del gasto y el ajuste de redondeo final."""
    expense = expense_service.create_expense(
        db=db_session,
        group_id=sample_group.id,
        paid_by_id=sample_group.members[0].id,
        description="  Taxi aeropuerto  ",
        amount=Decimal("100.00"),
    )

    splits = (
        db_session.query(ExpenseSplit)
        .filter(ExpenseSplit.expense_id == expense.id)
        .order_by(ExpenseSplit.amount)
        .all()
    )

    assert expense.description == "Taxi aeropuerto"
    assert [split.amount for split in splits] == [
        Decimal("33.33"),
        Decimal("33.33"),
        Decimal("33.34"),
    ]
    assert sum(split.amount for split in splits) == Decimal("100.00")


def test_create_expense_can_split_only_among_selected_members(db_session, sample_group):
    """Comprueba que un gasto pueda dividirse solo entre miembros indicados."""
    selected_members = [sample_group.members[0].id, sample_group.members[2].id]

    expense = expense_service.create_expense(
        db=db_session,
        group_id=sample_group.id,
        paid_by_id=sample_group.members[1].id,
        description="Hospedaje",
        amount=Decimal("80.00"),
        split_among_ids=selected_members,
    )

    splits = (
        db_session.query(ExpenseSplit)
        .filter(ExpenseSplit.expense_id == expense.id)
        .all()
    )

    assert len(splits) == 2
    assert {split.member_id for split in splits} == set(selected_members)
    assert {split.amount for split in splits} == {Decimal("40.00")}


@pytest.mark.parametrize(
    "case",
    [
        {
            "description": "   ",
            "amount": Decimal("10.00"),
            "paid_by_id": "member_0",
            "split_among_ids": None,
            "message": "La descripción es obligatoria",
        },
        {
            "description": "Cena",
            "amount": Decimal("0.00"),
            "paid_by_id": "member_0",
            "split_among_ids": None,
            "message": "El monto debe ser mayor a 0",
        },
        {
            "description": "Cena",
            "amount": Decimal("-5.00"),
            "paid_by_id": "member_0",
            "split_among_ids": None,
            "message": "El monto debe ser mayor a 0",
        },
        {
            "description": "Cena",
            "amount": Decimal("10.00"),
            "paid_by_id": "foreign",
            "split_among_ids": None,
            "message": "El pagador no es miembro del grupo",
        },
        {
            "description": "Cena",
            "amount": Decimal("10.00"),
            "paid_by_id": "member_0",
            "split_among_ids": ["member_0", "foreign"],
            "message": "Algunos miembros no pertenecen al grupo",
        },
        {
            "description": "Cena",
            "amount": Decimal("10.00"),
            "paid_by_id": "member_0",
            "split_among_ids": [],
            "message": "Debe haber al menos un miembro en la división",
        },
    ],
)
def test_create_expense_rejects_invalid_data(db_session, sample_group, case):
    """Verifica que la creación de gastos rechace combinaciones inválidas."""
    members = sample_group.members
    resolved_paid_by_id = members[0].id if case["paid_by_id"] == "member_0" else uuid4()

    resolved_split_ids = case["split_among_ids"]
    if case["split_among_ids"] is not None:
        resolved_split_ids = [
            members[0].id if member_id == "member_0" else uuid4()
            for member_id in case["split_among_ids"]
        ]

    with pytest.raises(ValueError, match=case["message"]):
        expense_service.create_expense(
            db=db_session,
            group_id=sample_group.id,
            paid_by_id=resolved_paid_by_id,
            description=case["description"],
            amount=case["amount"],
            split_among_ids=resolved_split_ids,
        )


def test_create_expense_rejects_unknown_group(db_session):
    """Asegura que no se creen gastos sobre grupos inexistentes."""
    with pytest.raises(ValueError, match="El grupo no existe"):
        expense_service.create_expense(
            db=db_session,
            group_id=uuid4(),
            paid_by_id=uuid4(),
            description="Cena",
            amount=Decimal("15.00"),
        )


def test_delete_expense_removes_existing_record(db_session, sample_group):
    """Comprueba que eliminar un gasto existente lo quite del listado."""
    expense = expense_service.create_expense(
        db=db_session,
        group_id=sample_group.id,
        paid_by_id=sample_group.members[0].id,
        description="Entrada",
        amount=Decimal("30.00"),
    )

    deleted = expense_service.delete_expense(db_session, sample_group.id, expense.id)

    assert deleted is True
    assert expense_service.list_expenses(db_session, sample_group.id) == []


def test_delete_expense_returns_false_when_not_found(db_session, sample_group):
    """Confirma que borrar un gasto inexistente devuelva False."""
    deleted = expense_service.delete_expense(db_session, sample_group.id, uuid4())

    assert deleted is False
