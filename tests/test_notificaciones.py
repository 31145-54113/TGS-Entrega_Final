"""Tests de urgencias de notificaciones."""
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient


def _iso(dias: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=dias)).isoformat()


def test_sin_notificaciones(client: TestClient, auth):
    r = client.get("/notificaciones", headers=auth)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 0
    assert body["notificaciones"] == []


def test_clasificacion_urgencias(client: TestClient, auth):
    client.post("/tareas", headers=auth, json={"titulo": "Vencida", "fecha_vencimiento": _iso(-1)})
    client.post("/tareas", headers=auth, json={"titulo": "Hoy", "fecha_vencimiento": _iso(0)})
    client.post("/tareas", headers=auth, json={"titulo": "Manana", "fecha_vencimiento": _iso(1)})
    client.post("/tareas", headers=auth, json={"titulo": "Semana", "fecha_vencimiento": _iso(4)})

    r = client.get("/notificaciones", headers=auth)
    body = r.json()
    assert body["total"] == 4
    assert body["por_urgencia"] == {"vencida": 1, "hoy": 1, "manana": 1, "esta_semana": 1}

    por_titulo = {n["titulo"]: n for n in body["notificaciones"]}
    assert por_titulo["Vencida"]["urgencia"] == "vencida"
    assert por_titulo["Vencida"]["dias_restantes"] == -1
    assert por_titulo["Hoy"]["dias_restantes"] == 0
    assert por_titulo["Manana"]["dias_restantes"] == 1


def test_no_incluye_lejanas(client: TestClient, auth):
    client.post("/tareas", headers=auth, json={"titulo": "Lejana", "fecha_vencimiento": _iso(15)})
    body = client.get("/notificaciones", headers=auth).json()
    assert body["total"] == 0


def test_no_incluye_completadas(client: TestClient, auth):
    r = client.post("/tareas", headers=auth, json={
        "titulo": "Hecha", "fecha_vencimiento": _iso(1), "estado": "completada",
    })
    body = client.get("/notificaciones", headers=auth).json()
    assert body["total"] == 0


def test_no_incluye_sin_fecha(client: TestClient, auth):
    client.post("/tareas", headers=auth, json={"titulo": "Sin fecha"})
    body = client.get("/notificaciones", headers=auth).json()
    assert body["total"] == 0


def test_aislamiento(client: TestClient, auth, segundo_usuario):
    client.post("/tareas", headers=auth, json={"titulo": "Mia", "fecha_vencimiento": _iso(1)})
    body = client.get("/notificaciones", headers=segundo_usuario).json()
    assert body["total"] == 0


def test_conteo_consistente_con_listado(client: TestClient, auth):
    client.post("/tareas", headers=auth, json={"titulo": "A", "fecha_vencimiento": _iso(-1)})
    client.post("/tareas", headers=auth, json={"titulo": "B", "fecha_vencimiento": _iso(0)})
    client.post("/tareas", headers=auth, json={"titulo": "C", "fecha_vencimiento": _iso(3)})

    listado = client.get("/notificaciones", headers=auth).json()
    conteo = client.get("/notificaciones/conteo", headers=auth).json()

    assert conteo["total"] == listado["total"]
    assert conteo["vencidas"] == listado["por_urgencia"]["vencida"]
    assert conteo["hoy"] == listado["por_urgencia"]["hoy"]
    assert conteo["manana"] == listado["por_urgencia"]["manana"]
    assert conteo["esta_semana"] == listado["por_urgencia"]["esta_semana"]
