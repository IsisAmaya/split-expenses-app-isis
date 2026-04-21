"""Servicio de lógica de negocio para grupos."""

from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from ..models import Group, Member


def create_group(db: Session, name: str, member_names: list[str]) -> Group:
    """Crea un grupo con sus miembros.

    Args:
        db: Sesión de base de datos.
        name: Nombre del grupo.
        member_names: Lista de nombres de los miembros.

    Returns:
        El grupo creado con sus miembros.

    Raises:
        ValueError: Si el nombre está vacío, hay menos de 2 miembros,
                    o hay nombres duplicados.
    """
    name = name.strip()
    if not name:
        raise ValueError("El nombre del grupo es obligatorio")
    if len(name) > 100:
        raise ValueError("El nombre no puede tener más de 100 caracteres")

    cleaned_names = [n.strip() for n in member_names if n.strip()]
    if len(cleaned_names) < 2:
        raise ValueError("El grupo debe tener al menos 2 miembros")

    if len(cleaned_names) != len(set(cleaned_names)):
        raise ValueError("Los nombres de los miembros deben ser únicos")

    group = Group(name=name)
    for member_name in cleaned_names:
        group.members.append(Member(name=member_name))

    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def get_group(db: Session, group_id: UUID) -> Group | None:
    """Obtiene un grupo por ID con sus miembros y gastos cargados.

    Args:
        db: Sesión de base de datos.
        group_id: ID del grupo.

    Returns:
        El grupo encontrado o None si no existe.
    """
    return (
        db.query(Group)
        .options(
            joinedload(Group.members),
            joinedload(Group.expenses),
        )
        .filter(Group.id == group_id)
        .first()
    )


def list_groups(db: Session) -> list[Group]:
    """Lista todos los grupos con el conteo de miembros.

    Args:
        db: Sesión de base de datos.

    Returns:
        Lista de todos los grupos.
    """
    return (
        db.query(Group)
        .options(joinedload(Group.members))
        .order_by(Group.created_at.desc())
        .all()
    )


def delete_group(db: Session, group_id: UUID) -> bool:
    """Elimina un grupo por ID.

    Args:
        db: Sesión de base de datos.
        group_id: ID del grupo a eliminar.

    Returns:
        ``True`` si el grupo existía y fue eliminado, ``False`` si no existía.
    """
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        return False

    db.delete(group)
    db.commit()
    return True
