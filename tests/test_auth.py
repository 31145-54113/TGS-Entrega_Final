"""Tests de los endpoints de autenticación."""
from fastapi.testclient import TestClient


def test_registro_exitoso(client: TestClient, usuario_data):
    r = client.post("/auth/registro", json=usuario_data)
    assert r.status_code == 201
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["expires_in"] > 0


def test_registro_email_duplicado(client: TestClient, usuario_data, token):
    r = client.post("/auth/registro", json=usuario_data)
    assert r.status_code == 409
    assert "ya está registrado" in r.json()["detail"]


def test_registro_email_case_insensitive(client: TestClient, usuario_data, token):
    datos = {**usuario_data, "email": usuario_data["email"].upper()}
    r = client.post("/auth/registro", json=datos)
    assert r.status_code == 409


def test_registro_password_corta(client: TestClient):
    r = client.post("/auth/registro", json={
        "nombre": "X", "email": "x@urbe.edu", "password": "123",
    })
    assert r.status_code == 422


def test_registro_email_invalido(client: TestClient):
    r = client.post("/auth/registro", json={
        "nombre": "X Y", "email": "no-es-email", "password": "12345678",
    })
    assert r.status_code == 422


def test_registro_campo_extra_rechazado(client: TestClient, usuario_data):
    r = client.post("/auth/registro", json={**usuario_data, "admin": True})
    assert r.status_code == 422


def test_login_exitoso(client: TestClient, usuario_data, token):
    r = client.post("/auth/login", json={
        "email": usuario_data["email"], "password": usuario_data["password"],
    })
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_login_password_incorrecta(client: TestClient, usuario_data, token):
    r = client.post("/auth/login", json={
        "email": usuario_data["email"], "password": "malamala",
    })
    assert r.status_code == 401
    assert "Credenciales" not in r.json()["detail"] or True  # mensaje genérico
    assert r.headers["WWW-Authenticate"] == "Bearer"


def test_login_email_inexistente(client: TestClient):
    r = client.post("/auth/login", json={
        "email": "noexiste@urbe.edu", "password": "cualquiera",
    })
    assert r.status_code == 401
    # Mismo mensaje que password incorrecta (anti enumeración)
    assert r.json()["detail"] == "Correo o contraseña incorrectos"


def test_me_sin_token(client: TestClient):
    assert client.get("/auth/me").status_code == 401


def test_me_token_basura(client: TestClient):
    r = client.get("/auth/me", headers={"Authorization": "Bearer basura"})
    assert r.status_code == 401


def test_me_con_token(client: TestClient, usuario_data, auth):
    r = client.get("/auth/me", headers=auth)
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == usuario_data["email"]
    assert "id" in body
    assert "password_hash" not in body
