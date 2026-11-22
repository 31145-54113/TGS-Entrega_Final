"""Tests del endpoint /dashboard."""
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient


def _iso(dias: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=dias)).isoformat()


def test_dashboard_vacio(client: TestClient, auth):
    r = client.get("/dashboard", headers=auth)
    assert r.status_code == 200
    body = r.json()

    assert body["resumen"]["total_tareas"] == 0
    assert body["resumen"]["por_estado"] == {"pendiente": 0, "en_progreso": 0, "completada": 0}
    assert body["resumen"]["por_prioridad"] == {"baja": 0, "media": 0, "alta": 0, "critica": 0}
    assert body["puntualidad"]["tasa"] is None
    assert body["semanal"]["variacion_pct"] is None
    assert body["tiempo_completado"]["promedio_horas"] is None
    assert len(body["serie_diaria"]) == 7


def test_dashboard_conteos(client: TestClient, auth):
    client.post("/tareas", headers=auth, json={"titulo": "A", "prioridad": "alta"})
    client.post("/tareas", headers=auth, json={"titulo": "B", "prioridad": "critica", "estado": "en_progreso"})
    client.post("/tareas", headers=auth, json={"titulo": "C", "estado": "completada"})

    r = client.get("/dashboard", headers=auth)
    body = r.json()

    assert body["resumen"]["total_tareas"] == 3
    assert body["resumen"]["por_estado"] == {"pendiente": 1, "en_progreso": 1, "completada": 1}
    assert body["resumen"]["por_prioridad"]["critica"] == 1
    assert body["resumen"]["por_prioridad"]["alta"] == 1


def test_dashboard_puntualidad(client: TestClient, auth):
    # A tiempo: se completa ahora, vencía en 5 días
    r = client.post("/tareas", headers=auth, json={
        "titulo": "A tiempo", "fecha_vencimiento": _iso(5),
    })
    client.patch(f"/tareas/{r.json()['id']}/estado", headers=auth, json={"estado": "completada"})

    # Tarde: vencía hace 2 días, se completa hoy
    r = client.post("/tareas", headers=auth, json={
        "titulo": "Tarde", "fecha_vencimiento": _iso(-2),
    })
    client.patch(f"/tareas/{r.json()['id']}/estado", headers=auth, json={"estado": "completada"})

    body = client.get("/dashboard", headers=auth).json()
    p = body["puntualidad"]
    assert p["completadas_con_fecha"] == 2
    assert p["a_tiempo"] == 1
    assert p["tarde"] == 1
    assert p["tasa"] == 50.0


def test_dashboard_serie_7_dias(client: TestClient, auth):
    r = client.post("/tareas", headers=auth, json={"titulo": "Hoy"})
    client.patch(f"/tareas/{r.json()['id']}/estado", headers=auth, json={"estado": "completada"})

    body = client.get("/dashboard", headers=auth).json()
    serie = body["serie_diaria"]
    assert len(serie) == 7
    assert serie[-1]["completadas"] == 1   # último elemento es hoy
