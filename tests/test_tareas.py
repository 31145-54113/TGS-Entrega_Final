"""Tests del CRUD de tareas, filtros y aislamiento entre usuarios."""
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient


def _iso(dias: int) -> str:
    """Fecha ISO a `dias` desde ahora (negativo = pasado)."""
    return (datetime.now(timezone.utc) + timedelta(days=dias)).isoformat()


def test_crear_tarea(client: TestClient, auth):
    r = client.post("/tareas", headers=auth, json={
        "titulo": "Informe TGS",
        "descripcion": "Fase 3",
        "prioridad": "alta",
        "fecha_vencimiento": _iso(5),
        "etiquetas": ["tgs", "urbe"],
    })
    assert r.status_code == 201
    body = r.json()
    assert body["titulo"] == "Informe TGS"
    assert body["estado"] == "pendiente"
    assert body["prioridad"] == "alta"
    assert body["etiquetas"] == ["tgs", "urbe"]
    assert body["completado_en"] is None
    assert body["id"] > 0


def test_crear_sin_auth(client: TestClient):
    r = client.post("/tareas", json={"titulo": "x"})
    assert r.status_code == 401


def test_crear_titulo_vacio(client: TestClient, auth):
    r = client.post("/tareas", headers=auth, json={"titulo": "   "})
    assert r.status_code == 422


def test_etiquetas_normalizadas(client: TestClient, auth):
    r = client.post("/tareas", headers=auth, json={
        "titulo": "T", "etiquetas": ["  TGS  ", "URBE", "tgs", ""],
    })
    assert r.status_code == 201
    assert r.json()["etiquetas"] == ["tgs", "urbe"]


def test_etiquetas_caracteres_prohibidos(client: TestClient, auth):
    r = client.post("/tareas", headers=auth, json={
        "titulo": "T", "etiquetas": ["mal,con,comas"],
    })
    assert r.status_code == 422


def test_listar_solo_propias(client: TestClient, auth, segundo_usuario):
    client.post("/tareas", headers=auth, json={"titulo": "A1"})
    client.post("/tareas", headers=auth, json={"titulo": "A2"})
    client.post("/tareas", headers=segundo_usuario, json={"titulo": "B1"})

    r = client.get("/tareas", headers=auth)
    assert r.status_code == 200
    titulos = {t["titulo"] for t in r.json()}
    assert titulos == {"A1", "A2"}


def test_get_de_otro_usuario_404(client: TestClient, auth, segundo_usuario):
    r = client.post("/tareas", headers=auth, json={"titulo": "Mia"})
    tarea_id = r.json()["id"]

    r2 = client.get(f"/tareas/{tarea_id}", headers=segundo_usuario)
    assert r2.status_code == 404


def test_patch_parcial(client: TestClient, auth):
    r = client.post("/tareas", headers=auth, json={
        "titulo": "Original", "descripcion": "algo", "prioridad": "baja",
    })
    tid = r.json()["id"]

    r2 = client.patch(f"/tareas/{tid}", headers=auth, json={"prioridad": "critica"})
    assert r2.status_code == 200
    body = r2.json()
    assert body["titulo"] == "Original"            # no se tocó
    assert body["descripcion"] == "algo"           # no se tocó
    assert body["prioridad"] == "critica"          # sí se cambió


def test_patch_limpiar_descripcion(client: TestClient, auth):
    r = client.post("/tareas", headers=auth, json={
        "titulo": "T", "descripcion": "algo",
    })
    tid = r.json()["id"]
    r2 = client.patch(f"/tareas/{tid}", headers=auth, json={"descripcion": None})
    assert r2.status_code == 200
    assert r2.json()["descripcion"] is None


def test_patch_sin_campos(client: TestClient, auth):
    r = client.post("/tareas", headers=auth, json={"titulo": "T"})
    tid = r.json()["id"]
    r2 = client.patch(f"/tareas/{tid}", headers=auth, json={})
    assert r2.status_code == 422


def test_cambiar_estado_setea_completado_en(client: TestClient, auth):
    r = client.post("/tareas", headers=auth, json={"titulo": "T"})
    tid = r.json()["id"]
    assert r.json()["completado_en"] is None

    r2 = client.patch(f"/tareas/{tid}/estado", headers=auth, json={"estado": "completada"})
    assert r2.status_code == 200
    assert r2.json()["completado_en"] is not None


def test_des_completar_limpia_completado_en(client: TestClient, auth):
    r = client.post("/tareas", headers=auth, json={"titulo": "T", "estado": "completada"})
    tid = r.json()["id"]
    assert r.json()["completado_en"] is not None

    r2 = client.patch(f"/tareas/{tid}/estado", headers=auth, json={"estado": "pendiente"})
    assert r2.json()["completado_en"] is None


def test_delete(client: TestClient, auth):
    r = client.post("/tareas", headers=auth, json={"titulo": "T"})
    tid = r.json()["id"]
    assert client.delete(f"/tareas/{tid}", headers=auth).status_code == 204
    assert client.get(f"/tareas/{tid}", headers=auth).status_code == 404


def test_filtro_por_estado_y_prioridad(client: TestClient, auth):
    client.post("/tareas", headers=auth, json={"titulo": "P1", "prioridad": "alta"})
    client.post("/tareas", headers=auth, json={"titulo": "P2", "prioridad": "baja"})
    client.post("/tareas", headers=auth, json={"titulo": "C1", "estado": "completada"})

    r = client.get("/tareas?estado=completada", headers=auth)
    assert {t["titulo"] for t in r.json()} == {"C1"}

    r = client.get("/tareas?prioridad=alta", headers=auth)
    assert {t["titulo"] for t in r.json()} == {"P1"}


def test_orden_por_prioridad(client: TestClient, auth):
    for p in ("baja", "critica", "media", "alta"):
        client.post("/tareas", headers=auth, json={"titulo": p, "prioridad": p})

    r = client.get("/tareas?orden_por=prioridad", headers=auth)
    prioridades = [t["prioridad"] for t in r.json()]
    assert prioridades == ["critica", "alta", "media", "baja"]


def test_filtro_vencidas(client: TestClient, auth):
    client.post("/tareas", headers=auth, json={"titulo": "Vencida", "fecha_vencimiento": _iso(-2)})
    client.post("/tareas", headers=auth, json={"titulo": "Futura", "fecha_vencimiento": _iso(5)})

    r = client.get("/tareas?vencidas=true", headers=auth)
    assert {t["titulo"] for t in r.json()} == {"Vencida"}
