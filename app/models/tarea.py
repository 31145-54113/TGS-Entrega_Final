"""Modelo de dominio de tarea."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class EstadoTarea(str, Enum):
    PENDIENTE = "pendiente"
    EN_PROGRESO = "en_progreso"
    COMPLETADA = "completada"


class PrioridadTarea(str, Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


@dataclass(frozen=True)
class Tarea:
    id: int
    usuario_id: int
    titulo: str
    descripcion: str | None
    estado: EstadoTarea
    prioridad: PrioridadTarea
    fecha_vencimiento: datetime | None
    etiquetas: list[str]
    completado_en: datetime | None
    creado_en: str
    actualizado_en: str
