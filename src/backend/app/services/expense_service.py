"""Servicio de lógica de negocio para gastos."""

from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from ..models import Expense, ExpenseSplit
from .common import get_group_with_members


def create_expense(
    db: Session,
    group_id: UUID,
    paid_by_id: UUID,
    description: str,
    amount: Decimal,
    split_among_ids: list[UUID] | None = None,
) -> Expense:
    """Crea un gasto y lo divide equitativamente entre los participantes.

    Args:
        db: Sesión de base de datos.
        group_id: ID del grupo.
        paid_by_id: ID del miembro que pagó.
        description: Descripción del gasto.
        amount: Monto total del gasto.
        split_among_ids: IDs de los miembros entre quienes se divide.
                         Si es None, se divide entre todos.

    Returns:
        El gasto creado con sus splits.

    Raises:
        ValueError: Si los datos son inválidos.
    """
    description = description.strip()
    if not description:
        raise ValueError("La descripción es obligatoria")

    amount = Decimal(str(amount))
    if amount <= 0:
        raise ValueError("El monto debe ser mayor a 0")

    # Verificar que el grupo existe
    group = get_group_with_members(db, group_id)
    if not group:
        raise ValueError("El grupo no existe")

    # Verificar que el pagador es miembro del grupo
    member_ids = {m.id for m in group.members}
    if paid_by_id not in member_ids:
        raise ValueError("El pagador no es miembro del grupo")

    # Determinar entre quiénes se divide
    if split_among_ids is None:
        split_members = group.members
    else:
        invalid = set(split_among_ids) - member_ids
        if invalid:
            raise ValueError("Algunos miembros no pertenecen al grupo")
        split_members = [m for m in group.members if m.id in set(split_among_ids)]

    if not split_members:
        raise ValueError("Debe haber al menos un miembro en la división")

    # Calcular división equitativa
    num_members = len(split_members)
    share = (amount / num_members).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    # Ajustar el último para que la suma sea exacta
    remainder = amount - (share * (num_members - 1))

    # Crear el gasto
    expense = Expense(
        group_id=group_id,
        paid_by_id=paid_by_id,
        description=description,
        amount=amount,
    )
    db.add(expense)
    db.flush()  # Para obtener el ID del expense

    # Crear los splits
    for i, member in enumerate(split_members):
        split_amount = remainder if i == num_members - 1 else share
        db.add(
            ExpenseSplit(
                expense_id=expense.id,
                member_id=member.id,
                amount=split_amount,
            )
        )

    db.commit()
    db.refresh(expense)
    return expense


def list_expenses(db: Session, group_id: UUID) -> list[Expense]:
    """Lista todos los gastos de un grupo, más recientes primero.

    Args:
        db: Sesión de base de datos.
        group_id: ID del grupo.

    Returns:
        Lista de gastos del grupo.
    """
    return (
        db.query(Expense)
        .options(
            joinedload(Expense.paid_by),
            joinedload(Expense.splits).joinedload(ExpenseSplit.member),
        )
        .filter(Expense.group_id == group_id)
        .order_by(Expense.created_at.desc())
        .all()
    )


def delete_expense(db: Session, group_id: UUID, expense_id: UUID) -> bool:
    """Elimina un gasto de un grupo.

    Args:
        db: Sesión de base de datos.
        group_id: ID del grupo.
        expense_id: ID del gasto a eliminar.

    Returns:
        True si se eliminó, False si no se encontró.
    """
    expense = (
        db.query(Expense)
        .filter(Expense.id == expense_id, Expense.group_id == group_id)
        .first()
    )
    if not expense:
        return False

    db.delete(expense)
    db.commit()
    return True
