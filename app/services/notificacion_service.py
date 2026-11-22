"""Lógica de negocio de notificaciones."""
from __future__ import annotations

import sqlite3

from app.models.tarea import EstadoTarea, PrioridadTarea
from app.repositories import notificacion_repo
from app.repositories.tarea_repo import _desde_db
from app.schemas.notificacion import (
    ConteoNotificacionesOut,
    ConteoPorUrgencia,
    NotificacionOut,
    NotificacionesOut,
    Urgencia,
)

# Por defecto, avisos de hasta 30 días atrás. Más antiguo se considera
# "abandonado" y se oculta para no saturar.
_DIAS_ATRAS_DEFAULT = 30


def _clasificar(dias_restantes: int) -> Urgencia:
    if dias_restantes < 0:
        return Urgencia.VENCIDA
    if dias_restantes == 0:
        return Urgencia.HOY
    if dias_restantes == 1:
        return Urgencia.MANANA
    return Urgencia.ESTA_SEMANA


def listar(
    conn: sqlite3.Connection,
    usuario_id: int,
    dias_atras: int = _DIAS_ATRAS_DEFAULT,
) -> NotificacionesOut:
    filas = notificacion_repo.tareas_con_aviso(conn, usuario_id, dias_atras)

    notificaciones: list[NotificacionOut] = []
    conteo = ConteoPorUrgencia()

    for fila in filas:
        urgencia = _clasificar(fila["dias_restantes"])
        notificaciones.append(
            NotificacionOut(
                tarea_id=fila["id"],
                titulo=fila["titulo"],
                estado=EstadoTarea(fila["estado"]),
                prioridad=PrioridadTarea(fila["prioridad"]),
                fecha_vencimiento=_desde_db(fila["fecha_vencimiento"]),
                urgencia=urgencia,
                dias_restantes=fila["dias_restantes"],
            )
        )
        setattr(conteo, urgencia.value, getattr(conteo, urgencia.value) + 1)

    return NotificacionesOut(
        total=len(notificaciones),
        por_urgencia=conteo,
        notificaciones=notificaciones,
    )


def conteo(
    conn: sqlite3.Connection,
    usuario_id: int,
    dias_atras: int = _DIAS_ATRAS_DEFAULT,
) -> ConteoNotificacionesOut:
    """Solo los números: útil para el badge sin pagar el payload completo."""
    filas = notificacion_repo.tareas_con_aviso(conn, usuario_id, dias_atras)

    por_urgencia = {"vencida": 0, "hoy": 0, "manana": 0, "esta_semana": 0}
    for fila in filas:
        por_urgencia[_clasificar(fila["dias_restantes"]).value] += 1

    return ConteoNotificacionesOut(
        total=len(filas),
        vencidas=por_urgencia["vencida"],
        hoy=por_urgencia["hoy"],
        manana=por_urgencia["manana"],
        esta_semana=por_urgencia["esta_semana"],
    )
