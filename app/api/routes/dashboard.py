"""Endpoint del dashboard analítico."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.db.connection import get_connection
from app.models.usuario import Usuario
from app.schemas.dashboard import DashboardOut
from app.services import dashboard_service

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard", response_model=DashboardOut)
def obtener_dashboard(
    usuario: Usuario = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_connection),
) -> DashboardOut:
    """Métricas de productividad del usuario autenticado.

    Incluye resumen, puntualidad, semana actual vs anterior, serie de los
    últimos 7 días y tiempo promedio/mediano de completado.
    """
    return dashboard_service.construir_dashboard(conn, usuario.id)
