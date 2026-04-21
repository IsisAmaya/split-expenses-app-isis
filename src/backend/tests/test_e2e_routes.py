"""Tests E2E del flujo principal a través de las rutas reales."""

from decimal import Decimal

from app.routes import expenses, groups
from app.schemas import ExpenseCreate, GroupCreate


def test_e2e_user_flow_from_group_creation_to_expense_deletion(db_session):
    """Recorre el flujo principal: grupo, gastos, balances, pagos y borrado."""
    group = groups.create_group(
        GroupCreate(name="Roadtrip", members=["Ana", "Beto", "Carla"]),
        db_session,
    )
    ana_id = group.members[0].id
    beto_id = group.members[1].id

    lunch = expenses.create_expense(
        group.id,
        ExpenseCreate(
            description="Almuerzo",
            amount=Decimal("60.00"),
            paid_by_id=ana_id,
            split_among_ids=None,
        ),
        db_session,
    )
    taxi = expenses.create_expense(
        group.id,
        ExpenseCreate(
            description="Taxi",
            amount=Decimal("30.00"),
            paid_by_id=beto_id,
            split_among_ids=[ana_id, beto_id],
        ),
        db_session,
    )

    detail = groups.get_group(group.id, db_session)
    assert detail.expense_count == 2

    expense_list = expenses.list_expenses(group.id, db_session)
    assert [expense.description for expense in expense_list] == ["Taxi", "Almuerzo"]

    balances = expenses.get_balances(group.id, db_session)
    assert {(item.member, item.balance) for item in balances} == {
        ("Ana", Decimal("25.00")),
        ("Beto", Decimal("-5.00")),
        ("Carla", Decimal("-20.00")),
    }

    settlements = expenses.get_settlements(group.id, db_session)
    assert [
        (item.from_member, item.to_member, item.amount) for item in settlements
    ] == [
        ("Carla", "Ana", Decimal("20.00")),
        ("Beto", "Ana", Decimal("5.00")),
    ]

    assert lunch.description == "Almuerzo"
    expenses.delete_expense(group.id, taxi.id, db_session)

    balances_after_delete = expenses.get_balances(group.id, db_session)
    assert {(item.member, item.balance) for item in balances_after_delete} == {
        ("Ana", Decimal("40.00")),
        ("Beto", Decimal("-20.00")),
        ("Carla", Decimal("-20.00")),
    }

    settlements_after_delete = expenses.get_settlements(group.id, db_session)
    assert [
        (item.from_member, item.to_member, item.amount)
        for item in settlements_after_delete
    ] == [
        ("Beto", "Ana", Decimal("20.00")),
        ("Carla", "Ana", Decimal("20.00")),
    ]
