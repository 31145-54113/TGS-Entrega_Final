"""Fixtures compartidas por toda la suite."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


@pytest.fixture
def db_aislada(tmp_path):
    """Redirige settings.db_path a una DB temporal y la restaura al salir."""
    original = settings.db_path
    object.__setattr__(settings, "db_path", tmp_path / "test.db")
    try:
        yield
    finally:
        object.__setattr__(settings, "db_path", original)


@pytest.fixture
def client(db_aislada):
    """TestClient con lifespan activo: init_db crea las tablas en la DB temporal."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def usuario_data() -> dict[str, str]:
    return {
        "nombre": "Usuario Test",
        "email": "test@urbe.edu",
        "password": "password123",
    }


@pytest.fixture
def token(client: TestClient, usuario_data: dict[str, str]) -> str:
    r = client.post("/auth/registro", json=usuario_data)
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


@pytest.fixture
def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def segundo_usuario(client: TestClient) -> dict[str, str]:
    """Registra un segundo usuario y devuelve su header de auth."""
    r = client.post(
        "/auth/registro",
        json={"nombre": "Otro", "email": "otro@urbe.edu", "password": "otro12345"},
    )
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
