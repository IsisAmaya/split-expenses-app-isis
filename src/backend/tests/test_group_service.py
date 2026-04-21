"""Tests unitarios para la lógica de grupos."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.services import group_service


def test_create_group_persists_clean_name_and_members(db_session):
    """Verifica que el grupo se cree con nombre y miembros normalizados."""
    group = group_service.create_group(
        db_session,
        "  Viaje de amigos  ",
        [" Ana ", "Beto", "  Carla  ", ""],
    )

    assert group.name == "Viaje de amigos"
    assert [member.name for member in group.members] == ["Ana", "Beto", "Carla"]


@pytest.mark.parametrize(
    ("name", "members", "message"),
    [
        ("   ", ["Ana", "Beto"], "El nombre del grupo es obligatorio"),
        ("Viaje", ["Ana"], "El grupo debe tener al menos 2 miembros"),
        ("Viaje", ["Ana", "Ana"], "Los nombres de los miembros deben ser únicos"),
        ("x" * 101, ["Ana", "Beto"], "El nombre no puede tener más de 100 caracteres"),
    ],
)
def test_create_group_rejects_invalid_data(db_session, name, members, message):
    """Comprueba que la creación de grupos invalide entradas incorrectas."""
    with pytest.raises(ValueError, match=message):
        group_service.create_group(db_session, name, members)


def test_get_group_returns_members_and_expenses(db_session, sample_group):
    """Confirma que obtener un grupo cargue relaciones de miembros y gastos."""
    created_expense = sample_group.expenses
    assert created_expense == []

    fetched_group = group_service.get_group(db_session, sample_group.id)

    assert fetched_group is not None
    assert fetched_group.id == sample_group.id
    assert [member.name for member in fetched_group.members] == ["Ana", "Beto", "Carla"]
    assert fetched_group.expenses == []


def test_list_groups_returns_newest_first(db_session):
    """Asegura que el listado de grupos respete el orden más reciente primero."""
    older_group = group_service.create_group(db_session, "Viejo", ["Ana", "Beto"])
    newer_group = group_service.create_group(db_session, "Nuevo", ["Caro", "Diego"])

    older_group.created_at = datetime.now(timezone.utc) - timedelta(days=1)
    newer_group.created_at = datetime.now(timezone.utc)
    db_session.commit()

    groups = group_service.list_groups(db_session)

    assert [group.name for group in groups] == ["Nuevo", "Viejo"]


def test_delete_group_removes_group_and_related_data(db_session, sample_expense):
    """Asegura que borrar un grupo elimine también sus relaciones en cascada."""
    group_id = sample_expense.group_id

    deleted = group_service.delete_group(db_session, group_id)

    assert deleted is True
    assert group_service.get_group(db_session, group_id) is None
    assert group_service.list_groups(db_session) == []


def test_delete_group_returns_false_when_group_does_not_exist(db_session):
    """Confirma que intentar borrar un grupo inexistente no rompe el servicio."""
    deleted = group_service.delete_group(db_session, uuid4())

    assert deleted is False
