"""Servicio de cálculo de balances y transferencias optimizadas."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from ..models import Expense
from .common import get_group_with_members


def calculate_balances(db: Session, group_id: UUID) -> dict[str, Decimal]:
    """Calcula el balance neto de cada miembro del grupo.

    Balance positivo = le deben dinero.
    Balance negativo = debe dinero.

    Args:
        db: Sesión de base de datos.
        group_id: ID del grupo.

    Returns:
        Diccionario {nombre_miembro: balance_neto}.

    Raises:
        ValueError: Si el grupo no existe.
    """
    group = get_group_with_members(db, group_id)
    if not group:
        raise ValueError("El grupo no existe")

    # Inicializar balances en 0
    balances: dict[UUID, Decimal] = {m.id: Decimal("0.00") for m in group.members}
    member_names: dict[UUID, str] = {m.id: m.name for m in group.members}

    # Obtener todos los gastos del grupo con sus splits
    expenses = (
        db.query(Expense)
        .options(joinedload(Expense.splits))
        .filter(Expense.group_id == group_id)
        .all()
    )

    for expense in expenses:
        # El que pagó suma lo que pagó
        balances[expense.paid_by_id] += Decimal(str(expense.amount))

        # Cada participante resta lo que le corresponde
        for split in expense.splits:
            balances[split.member_id] -= Decimal(str(split.amount))

    return {member_names[mid]: balance for mid, balance in balances.items()}


def calculate_settlements(
    db: Session, group_id: UUID
) -> list[dict[str, str | Decimal]]:
    """Calcula las transferencias mínimas para saldar todas las deudas.

    Usa un algoritmo greedy: empareja el mayor deudor con el mayor
    acreedor hasta que todos los balances sean 0.

    Args:
        db: Sesión de base de datos.
        group_id: ID del grupo.

    Returns:
        Lista de transferencias:
        [{"from": nombre, "to": nombre, "amount": monto}]
    """
    balances = calculate_balances(db, group_id)

    # Separar en deudores y acreedores
    debtors: list[tuple[str, Decimal]] = []
    creditors: list[tuple[str, Decimal]] = []

    for name, balance in balances.items():
        if balance < 0:
            debtors.append((name, abs(balance)))
        elif balance > 0:
            creditors.append((name, balance))

    # Ordenar por monto (mayor primero)
    debtors.sort(key=lambda x: x[1], reverse=True)
    creditors.sort(key=lambda x: x[1], reverse=True)

    settlements: list[dict[str, str | Decimal]] = []

    i, j = 0, 0
    while i < len(debtors) and j < len(creditors):
        debtor_name, debt = debtors[i]
        creditor_name, credit = creditors[j]

        # La transferencia es el mínimo de ambos
        transfer = min(debt, credit)

        if transfer > Decimal("0.00"):
            settlements.append(
                {
                    "from": debtor_name,
                    "to": creditor_name,
                    "amount": transfer,
                }
            )

        # Ajustar montos restantes
        debtors[i] = (debtor_name, debt - transfer)
        creditors[j] = (creditor_name, credit - transfer)

        if debtors[i][1] == Decimal("0.00"):
            i += 1
        if creditors[j][1] == Decimal("0.00"):
            j += 1

    return settlements
