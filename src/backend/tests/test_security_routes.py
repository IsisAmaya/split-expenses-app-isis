"""Tests de seguridad para validaciones y errores controlados."""

from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.routes import expenses, groups
from app.schemas import ExpenseCreate, GroupCreate


def test_security_group_schema_rejects_empty_member_list():
    """Asegura que el schema impida grupos sin la cantidad mínima de miembros."""
    with pytest.raises(ValidationError):
        GroupCreate(name="Grupo inválido", members=["Ana"])


def test_security_expense_schema_rejects_invalid_uuid():
    """Verifica que el schema invalide IDs con formato UUID incorrecto."""
    with pytest.raises(ValidationError):
        ExpenseCreate(
            description="Cena",
            amount=Decimal("30.00"),
            paid_by_id="not-a-uuid",
            split_among_ids=None,
        )


def test_security_rejects_non_member_as_expense_payer(db_session):
    """Valida que un pagador ajeno al grupo reciba un error controlado."""
    group = groups.create_group(
        GroupCreate(name="Seguridad", members=["Ana", "Beto"]),
        db_session,
    )

    with pytest.raises(HTTPException) as exc_info:
        expenses.create_expense(
            group.id,
            ExpenseCreate(
                description="Cena",
                amount=Decimal("30.00"),
                paid_by_id=uuid4(),
                split_among_ids=None,
            ),
            db_session,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "El pagador no es miembro del grupo"


def test_security_returns_404_for_unknown_group_lookup(db_session):
    """Comprueba que consultar un grupo inexistente no exponga detalles internos."""
    with pytest.raises(HTTPException) as exc_info:
        groups.get_group(uuid4(), db_session)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Grupo no encontrado"


def test_security_treats_sql_like_input_as_plain_text(db_session):
    """Comprueba que entradas con apariencia de SQL se manejen como datos."""
    payload = GroupCreate(
        name="Viaje'; DROP TABLE groups;--",
        members=["Ana", "Beto"],
    )

    created_group = groups.create_group(payload, db_session)
    group_list = groups.list_groups(db_session)

    assert created_group.name == payload.name
    assert group_list[0].name == payload.name
