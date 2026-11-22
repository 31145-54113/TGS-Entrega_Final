"""Schemas de respuesta del dashboard analítico."""
from __future__ import annotations

from pydantic import BaseModel


class ConteoPorEstado(BaseModel):
    pendiente: int = 0
    en_progreso: int = 0
    completada: int = 0


class ConteoPorPrioridad(BaseModel):
    baja: int = 0
    media: int = 0
    alta: int = 0
    critica: int = 0


class ResumenOut(BaseModel):
    total_tareas: int
    por_estado: ConteoPorEstado
    por_prioridad: ConteoPorPrioridad
    vencidas_pendientes: int
    proximas_7_dias: int


class PuntualidadOut(BaseModel):
    completadas_con_fecha: int
    a_tiempo: int
    tarde: int
    tasa: float | None   # % (0–100); None si no hay datos


class SemanalOut(BaseModel):
    ultimos_7_dias: int
    semana_anterior: int
    variacion_pct: float | None   # None si semana_anterior = 0
    promedio_diario: float


class DiaCompletadas(BaseModel):
    fecha: str          # "YYYY-MM-DD"
    completadas: int


class TiempoCompletadoOut(BaseModel):
    promedio_horas: float | None
    mediana_horas: float | None


class DashboardOut(BaseModel):
    resumen: ResumenOut
    puntualidad: PuntualidadOut
    semanal: SemanalOut
    serie_diaria: list[DiaCompletadas]
    tiempo_completado: TiempoCompletadoOut
