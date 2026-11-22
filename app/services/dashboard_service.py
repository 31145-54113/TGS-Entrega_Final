"""Lógica de negocio del dashboard analítico."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

from app.models.tarea import EstadoTarea, PrioridadTarea
from app.repositories import dashboard_repo
from app.schemas.dashboard import (
    ConteoPorEstado,
    ConteoPorPrioridad,
    DashboardOut,
    DiaCompletadas,
    PuntualidadOut,
    ResumenOut,
    SemanalOut,
    TiempoCompletadoOut,
)

_DIAS_SERIE = 7


def _mediana(valores: list[float]) -> float | None:
    if not valores:
        return None
    ordenados = sorted(valores)
    n = len(ordenados)
    if n % 2 == 1:
        return round(ordenados[n // 2], 2)
    return round((ordenados[n // 2 - 1] + ordenados[n // 2]) / 2, 2)


def _redondear(valor: float, decimales: int = 2) -> float:
    return round(valor, decimales)


def construir_dashboard(conn: sqlite3.Connection, usuario_id: int) -> DashboardOut:
    # --- Resumen ---
    total = dashboard_repo.total_tareas(conn, usuario_id)
    estados = dashboard_repo.por_estado(conn, usuario_id)
    prioridades = dashboard_repo.por_prioridad(conn, usuario_id)
    vencidas = dashboard_repo.vencidas_pendientes(conn, usuario_id)
    proximas = dashboard_repo.proximas_dias(conn, usuario_id, 7)

    resumen = ResumenOut(
        total_tareas=total,
        por_estado=ConteoPorEstado(
            pendiente=estados.get(EstadoTarea.PENDIENTE.value, 0),
            en_progreso=estados.get(EstadoTarea.EN_PROGRESO.value, 0),
            completada=estados.get(EstadoTarea.COMPLETADA.value, 0),
        ),
        por_prioridad=ConteoPorPrioridad(
            baja=prioridades.get(PrioridadTarea.BAJA.value, 0),
            media=prioridades.get(PrioridadTarea.MEDIA.value, 0),
            alta=prioridades.get(PrioridadTarea.ALTA.value, 0),
            critica=prioridades.get(PrioridadTarea.CRITICA.value, 0),
        ),
        vencidas_pendientes=vencidas,
        proximas_7_dias=proximas,
    )

    # --- Puntualidad ---
    completadas_con_fecha, a_tiempo = dashboard_repo.puntualidad(conn, usuario_id)
    tarde = completadas_con_fecha - a_tiempo
    tasa = _redondear((a_tiempo / completadas_con_fecha) * 100) if completadas_con_fecha > 0 else None
    puntualidad = PuntualidadOut(
        completadas_con_fecha=completadas_con_fecha,
        a_tiempo=a_tiempo,
        tarde=tarde,
        tasa=tasa,
    )

    # --- Semanal ---
    ultimos_7 = dashboard_repo.completadas_entre(conn, usuario_id, "-7 days")
    anterior = dashboard_repo.completadas_entre(conn, usuario_id, "-14 days", "-7 days")
    if anterior > 0:
        variacion = _redondear(((ultimos_7 - anterior) / anterior) * 100)
    else:
        variacion = None
    semanal = SemanalOut(
        ultimos_7_dias=ultimos_7,
        semana_anterior=anterior,
        variacion_pct=variacion,
        promedio_diario=_redondear(ultimos_7 / 7),
    )

    # --- Serie diaria (rellenando días sin actividad con 0) ---
    filas = dashboard_repo.completadas_por_dia(conn, usuario_id, _DIAS_SERIE)
    por_dia = {f["dia"]: f["n"] for f in filas}
    hoy = datetime.now(timezone.utc).date()
    serie = [
        DiaCompletadas(
            fecha=(hoy - timedelta(days=i)).isoformat(),
            completadas=por_dia.get((hoy - timedelta(days=i)).isoformat(), 0),
        )
        for i in range(_DIAS_SERIE - 1, -1, -1)
    ]

    # --- Tiempo de completado ---
    tiempos = dashboard_repo.tiempos_completado_horas(conn, usuario_id)
    if tiempos:
        promedio = _redondear(sum(tiempos) / len(tiempos))
        mediana = _mediana(tiempos)
    else:
        promedio = None
        mediana = None
    tiempo_completado = TiempoCompletadoOut(promedio_horas=promedio, mediana_horas=mediana)

    return DashboardOut(
        resumen=resumen,
        puntualidad=puntualidad,
        semanal=semanal,
        serie_diaria=serie,
        tiempo_completado=tiempo_completado,
    )
