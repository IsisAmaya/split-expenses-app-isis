"""Rutas API para gestión de grupos."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..exceptions import bad_request, not_found
from ..schemas import GroupCreate, GroupListItem, GroupResponse
from ..services import group_service

router = APIRouter(prefix="/api/groups", tags=["groups"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/", response_model=GroupResponse, status_code=201)
def create_group(payload: GroupCreate, db: DbSession):
    """Crea un grupo con sus miembros."""
    try:
        group = group_service.create_group(db, payload.name, payload.members)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc

    return _to_group_response(group)


@router.get("/", response_model=list[GroupListItem])
def list_groups(db: DbSession):
    """Lista todos los grupos."""
    groups = group_service.list_groups(db)
    return [
        GroupListItem(
            id=g.id,
            name=g.name,
            member_count=len(g.members),
            created_at=g.created_at,
        )
        for g in groups
    ]


@router.get("/{group_id}", response_model=GroupResponse)
def get_group(group_id: UUID, db: DbSession):
    """Obtiene el detalle de un grupo."""
    group = group_service.get_group(db, group_id)
    if not group:
        raise not_found("Grupo no encontrado")

    return _to_group_response(group)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(group_id: UUID, db: DbSession):
    """Elimina un grupo existente."""
    deleted = group_service.delete_group(db, group_id)
    if not deleted:
        raise not_found("Grupo no encontrado")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _to_group_response(group) -> GroupResponse:
    """Convierte un modelo Group a su schema de respuesta."""
    return GroupResponse(
        id=group.id,
        name=group.name,
        members=[{"id": m.id, "name": m.name} for m in group.members],
        expense_count=len(group.expenses),
        created_at=group.created_at,
    )
