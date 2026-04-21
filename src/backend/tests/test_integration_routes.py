"""Tests de integración entre rutas, schemas, servicios y persistencia."""

from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.routes import expenses, groups
from app.schemas import ExpenseCreate, GroupCreate


pytestmark = pytest.mark.integration


def test_integration_create_group_route_persists_and_lists_group(db_session):
    """Verifica que la ruta cree un grupo persistente y visible en listados."""
    created_group = groups.create_group(
        GroupCreate(name="Integracion", members=["Ana", "Beto", "Carla"]),
        db_session,
    )

    listed_groups = groups.list_groups(db_session)
    fetched_group = groups.get_group(created_group.id, db_session)

    assert created_group.name == "Integracion"
    assert len(created_group.members) == 3
    assert len(listed_groups) == 1
    assert listed_groups[0].id == created_group.id
    assert fetched_group.id == created_group.id
    assert fetched_group.expense_count == 0


def test_integration_expense_routes_update_group_balances_and_cleanup(db_session):
    """Comprueba que crear y borrar gastos actualice detalle y balances del grupo."""
    group = groups.create_group(
        GroupCreate(name="Viaje Integracion", members=["Ana", "Beto", "Carla"]),
        db_session,
    )

    expense = expenses.create_expense(
        group.id,
        ExpenseCreate(
            description="Hotel",
            amount=Decimal("90.00"),
            paid_by_id=group.members[0].id,
            split_among_ids=None,
        ),
        db_session,
    )

    detail_after_create = groups.get_group(group.id, db_session)
    balances_after_create = expenses.get_balances(group.id, db_session)

    assert expense.paid_by == "Ana"
    assert detail_after_create.expense_count == 1
    assert {(item.member, item.balance) for item in balances_after_create} == {
        ("Ana", Decimal("60.00")),
        ("Beto", Decimal("-30.00")),
        ("Carla", Decimal("-30.00")),
    }

    delete_result = expenses.delete_expense(group.id, expense.id, db_session)
    detail_after_delete = groups.get_group(group.id, db_session)
    balances_after_delete = expenses.get_balances(group.id, db_session)

    assert delete_result is None
    assert detail_after_delete.expense_count == 0
    assert {(item.member, item.balance) for item in balances_after_delete} == {
        ("Ana", Decimal("0.00")),
        ("Beto", Decimal("0.00")),
        ("Carla", Decimal("0.00")),
    }


def test_integration_route_maps_missing_group_to_http_404(db_session):
    """Asegura que obtener un grupo inexistente se traduzca a un 404 controlado."""
    with pytest.raises(HTTPException) as exc_info:
        groups.get_group(uuid4(), db_session)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Grupo no encontrado"


def test_integration_delete_group_route_removes_group_and_returns_204(db_session):
    """Verifica que la ruta borre un grupo existente y lo saque del listado."""
    group = groups.create_group(
        GroupCreate(name="Borrar Integracion", members=["Ana", "Beto", "Carla"]),
        db_session,
    )

    response = groups.delete_group(group.id, db_session)
    listed_groups = groups.list_groups(db_session)

    assert response.status_code == 204
    assert listed_groups == []


def test_integration_delete_group_route_maps_missing_group_to_http_404(db_session):
    """Asegura que borrar un grupo inexistente responda con 404 controlado."""
    with pytest.raises(HTTPException) as exc_info:
        groups.delete_group(uuid4(), db_session)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Grupo no encontrado"


def test_integration_route_maps_invalid_expense_to_http_400(db_session):
    """Valida que un gasto inválido se traduzca a un 400 desde la ruta."""
    group = groups.create_group(
        GroupCreate(name="Errores Integracion", members=["Ana", "Beto"]),
        db_session,
    )

    with pytest.raises(HTTPException) as exc_info:
        expenses.create_expense(
            group.id,
            ExpenseCreate(
                description="Cena",
                amount=Decimal("10.00"),
                paid_by_id=uuid4(),
                split_among_ids=None,
            ),
            db_session,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "El pagador no es miembro del grupo"
