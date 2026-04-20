"""Rutas API para gestión de gastos, balances y transferencias."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..exceptions import bad_request, not_found
from ..schemas import (
    BalanceResponse,
    ExpenseCreate,
    ExpenseResponse,
    ExpenseSplitResponse,
    SettlementResponse,
)
from ..services import balance_service, expense_service

router = APIRouter(prefix="/api/groups/{group_id}", tags=["expenses"])


@router.post("/expenses", response_model=ExpenseResponse, status_code=201)
def create_expense(
    group_id: UUID,
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
):
    """Registra un gasto en el grupo."""
    try:
        expense = expense_service.create_expense(
            db=db,
            group_id=group_id,
            paid_by_id=payload.paid_by_id,
            description=payload.description,
            amount=payload.amount,
            split_among_ids=payload.split_among_ids,
        )
    except ValueError as exc:
        raise bad_request(str(exc)) from exc

    return _to_expense_response(expense)


@router.get("/expenses", response_model=list[ExpenseResponse])
def list_expenses(group_id: UUID, db: Session = Depends(get_db)):
    """Lista todos los gastos del grupo."""
    expenses = expense_service.list_expenses(db, group_id)
    return [_to_expense_response(e) for e in expenses]


@router.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(
    group_id: UUID,
    expense_id: UUID,
    db: Session = Depends(get_db),
):
    """Elimina un gasto del grupo."""
    deleted = expense_service.delete_expense(db, group_id, expense_id)
    if not deleted:
        raise not_found("Gasto no encontrado")


@router.get("/balances", response_model=list[BalanceResponse])
def get_balances(group_id: UUID, db: Session = Depends(get_db)):
    """Calcula los balances de cada miembro del grupo."""
    try:
        balances = balance_service.calculate_balances(db, group_id)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc

    return [
        BalanceResponse(member=name, balance=balance)
        for name, balance in balances.items()
    ]


@router.get("/settlements", response_model=list[SettlementResponse])
def get_settlements(group_id: UUID, db: Session = Depends(get_db)):
    """Calcula las transferencias mínimas para saldar deudas."""
    try:
        settlements = balance_service.calculate_settlements(db, group_id)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc

    return [
        SettlementResponse(
            from_member=s["from"],
            to_member=s["to"],
            amount=s["amount"],
        )
        for s in settlements
    ]


def _to_expense_response(expense) -> ExpenseResponse:
    """Convierte un modelo Expense a su schema de respuesta."""
    return ExpenseResponse(
        id=expense.id,
        description=expense.description,
        amount=expense.amount,
        paid_by=expense.paid_by.name,
        splits=[
            ExpenseSplitResponse(
                member_name=split.member.name,
                amount=split.amount,
            )
            for split in expense.splits
        ],
        created_at=expense.created_at,
    )
