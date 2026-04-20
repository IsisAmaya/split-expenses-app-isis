"""Funciones compartidas entre servicios."""

from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from ..models import Group


def get_group_with_members(db: Session, group_id: UUID) -> Group | None:
    """Obtiene un grupo con sus miembros cargados.

    Args:
        db: Sesión de base de datos.
        group_id: ID del grupo.

    Returns:
        El grupo encontrado o None si no existe.
    """
    return (
        db.query(Group)
        .options(joinedload(Group.members))
        .filter(Group.id == group_id)
        .first()
    )
