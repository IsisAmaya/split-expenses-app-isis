"""Fixtures compartidas para tests unitarios del backend."""

# pylint: disable=redefined-outer-name

from collections.abc import Iterator
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.services import expense_service, group_service


@pytest.fixture()
def db_session() -> Iterator[Session]:
    """Entrega una sesión aislada sobre SQLite en memoria."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def sample_group(db_session: Session):
    """Crea un grupo base para reutilizar en pruebas."""
    return group_service.create_group(db_session, "Viaje", ["Ana", "Beto", "Carla"])


@pytest.fixture()
def sample_expense(db_session: Session, sample_group):
    """Crea un gasto base dividido entre todos los miembros."""
    return expense_service.create_expense(
        db=db_session,
        group_id=sample_group.id,
        paid_by_id=sample_group.members[0].id,
        description="Cena",
        amount=Decimal("90.00"),
    )
