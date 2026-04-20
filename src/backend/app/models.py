"""Modelos ORM de la aplicación."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base


class Group(Base):
    """Modelo de grupo de gastos compartidos."""

    __tablename__ = "groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    members = relationship(
        "Member", back_populates="group", cascade="all, delete-orphan"
    )
    expenses = relationship(
        "Expense", back_populates="group", cascade="all, delete-orphan"
    )


class Member(Base):
    """Modelo de miembro de un grupo."""

    __tablename__ = "members"
    __table_args__ = (
        UniqueConstraint("group_id", "name", name="uq_member_group_name"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(
        UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(50), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    group = relationship("Group", back_populates="members")
    expenses_paid = relationship("Expense", back_populates="paid_by")
    splits = relationship(
        "ExpenseSplit", back_populates="member", cascade="all, delete-orphan"
    )


class Expense(Base):
    """Modelo de gasto registrado en un grupo."""

    __tablename__ = "expenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(
        UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False
    )
    paid_by_id = Column(
        UUID(as_uuid=True),
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
    )
    description = Column(String(200), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    group = relationship("Group", back_populates="expenses")
    paid_by = relationship("Member", back_populates="expenses_paid")
    splits = relationship(
        "ExpenseSplit", back_populates="expense", cascade="all, delete-orphan"
    )


class ExpenseSplit(Base):
    """Modelo de la división de un gasto entre miembros."""

    __tablename__ = "expense_splits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expense_id = Column(
        UUID(as_uuid=True),
        ForeignKey("expenses.id", ondelete="CASCADE"),
        nullable=False,
    )
    member_id = Column(
        UUID(as_uuid=True),
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
    )
    amount = Column(Numeric(12, 2), nullable=False)

    expense = relationship("Expense", back_populates="splits")
    member = relationship("Member", back_populates="splits")
