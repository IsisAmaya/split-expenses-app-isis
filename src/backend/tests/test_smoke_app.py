"""Tests de humo para verificar una aplicación ya desplegada en AWS."""

# pylint: disable=redefined-outer-name

import os

import httpx
import pytest


pytestmark = pytest.mark.smoke


def _deployed_base_url() -> str:
    """Obtiene la URL base del despliegue a validar."""
    base_url = (
        os.getenv("DEPLOYED_APP_BASE_URL")
        or os.getenv("SMOKE_BASE_URL")
        or os.getenv("APP_BASE_URL")
    )
    if not base_url:
        pytest.skip(
            "Define DEPLOYED_APP_BASE_URL, SMOKE_BASE_URL o APP_BASE_URL para smoke tests."
        )
    return base_url.rstrip("/")


@pytest.fixture()
def smoke_http_client() -> httpx.Client:
    """Entrega un cliente HTTP para validar el despliegue."""
    return httpx.Client(
        base_url=_deployed_base_url(), timeout=15.0, follow_redirects=True
    )


def test_smoke_frontend_homepage_is_served(smoke_http_client: httpx.Client):
    """Comprueba que el frontend principal cargue correctamente."""
    response = smoke_http_client.get("/")

    assert response.status_code == 200
    assert "Splitwise Lite" in response.text


def test_smoke_health_endpoint_reports_healthy(smoke_http_client: httpx.Client):
    """Verifica que el health check exponga backend y base de datos sanos."""
    response = smoke_http_client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"] == "healthy"


def test_smoke_groups_endpoint_returns_success(smoke_http_client: httpx.Client):
    """Asegura que el endpoint principal de grupos responda exitosamente."""
    response = smoke_http_client.get("/api/groups/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
