"""Schemas de notificaciones (avisos de vencimiento)."""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from app.models.tarea import EstadoTarea, PrioridadTarea


class Urgencia(str, Enum):
    VENCIDA = "vencida"
    HOY = "hoy"
    MANANA = "manana"
    ESTA_SEMANA = "esta_semana"


class NotificacionOut(BaseModel):
    """Una tarea que requiere atención por su fecha de vencimiento."""

    tarea_id: int
    titulo: str
    estado: EstadoTarea
    prioridad: PrioridadTarea
    fecha_vencimiento: datetime
    urgencia: Urgencia
    dias_restantes: int    # negativo si vencida, 0 si hoy, 1 si mañana, etc.


class ConteoPorUrgencia(BaseModel):
    vencida: int = 0
    hoy: int = 0
    manana: int = 0
    esta_semana: int = 0


class NotificacionesOut(BaseModel):
    total: int
    por_urgencia: ConteoPorUrgencia
    notificaciones: list[NotificacionOut]


class ConteoNotificacionesOut(BaseModel):
    """Respuesta ligera para el badge del header."""

    total: int
    vencidas: int
    hoy: int
    manana: int
    esta_semana: int
