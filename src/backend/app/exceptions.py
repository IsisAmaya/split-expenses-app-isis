"""Manejo centralizado de excepciones HTTP."""

from fastapi import HTTPException, status


def not_found(detail: str = "Recurso no encontrado") -> HTTPException:
    """Genera una excepción 404."""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=detail,
    )


def bad_request(detail: str) -> HTTPException:
    """Genera una excepción 400."""
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail,
    )
