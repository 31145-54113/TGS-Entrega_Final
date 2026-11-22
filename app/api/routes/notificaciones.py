"""Endpoints de notificaciones (avisos de vencimiento)."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_user
from app.db.connection import get_connection
from app.models.usuario import Usuario
from app.schemas.notificacion import ConteoNotificacionesOut, NotificacionesOut
from app.services import notificacion_service

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])


@router.get("", response_model=NotificacionesOut)
def listar_notificaciones(
    dias_atras: int = Query(
        default=30, ge=0, le=365,
        description="Cuántos días hacia atrás mirar para tareas vencidas",
    ),
    usuario: Usuario = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_connection),
) -> NotificacionesOut:
    """Tareas no completadas que vencen pronto o ya vencieron."""
    return notificacion_service.listar(conn, usuario.id, dias_atras)


@router.get("/conteo", response_model=ConteoNotificacionesOut)
def conteo_notificaciones(
    dias_atras: int = Query(default=30, ge=0, le=365),
    usuario: Usuario = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_connection),
) -> ConteoNotificacionesOut:
    """Solo los conteos, para el badge del header (payload liviano)."""
    return notificacion_service.conteo(conn, usuario.id, dias_atras)
