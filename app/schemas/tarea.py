"""Schemas Pydantic de tareas."""
from __future__ import annotations

from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.tarea import EstadoTarea, PrioridadTarea

_CARACTERES_TAG_PROHIBIDOS = {",", "%", "_", "\\"}


def _limpiar_etiquetas(valor: list[str] | None) -> list[str] | None:
    if valor is None:
        return None
    resultado: list[str] = []
    for et in valor:
        if not isinstance(et, str):
            raise ValueError("Cada etiqueta debe ser texto")
        limpia = et.strip().lower()
        if not limpia:
            continue
        if len(limpia) > 30:
            raise ValueError(f"Etiqueta demasiado larga: '{limpia}' (máx 30)")
        if any(c in limpia for c in _CARACTERES_TAG_PROHIBIDOS):
            raise ValueError(f"Etiqueta con carácter no permitido: '{limpia}'")
        if limpia not in resultado:
            resultado.append(limpia)
    if len(resultado) > 10:
        raise ValueError("Máximo 10 etiquetas por tarea")
    return resultado


class TareaCreate(BaseModel):
    """Datos para crear una tarea."""

    model_config = ConfigDict(extra="forbid")

    titulo: str = Field(min_length=1, max_length=200)
    descripcion: str | None = Field(default=None, max_length=5000)
    estado: EstadoTarea = EstadoTarea.PENDIENTE
    prioridad: PrioridadTarea = PrioridadTarea.MEDIA
    fecha_vencimiento: datetime | None = None
    etiquetas: list[str] = Field(default_factory=list)

    @field_validator("titulo", "descripcion", mode="before")
    @classmethod
    def _limpiar_texto(cls, v: object) -> object:
        return v.strip() if isinstance(v, str) else v

    @field_validator("etiquetas")
    @classmethod
    def _validar_etiquetas(cls, v: list[str]) -> list[str]:
        return _limpiar_etiquetas(v) or []


class TareaUpdate(BaseModel):
    """Actualización parcial: solo los campos enviados se modifican."""

    model_config = ConfigDict(extra="forbid")

    titulo: str | None = Field(default=None, min_length=1, max_length=200)
    descripcion: str | None = Field(default=None, max_length=5000)
    estado: EstadoTarea | None = None
    prioridad: PrioridadTarea | None = None
    fecha_vencimiento: datetime | None = None
    etiquetas: list[str] | None = None

    @field_validator("titulo", "descripcion", mode="before")
    @classmethod
    def _limpiar_texto(cls, v: object) -> object:
        return v.strip() if isinstance(v, str) else v

    @field_validator("etiquetas")
    @classmethod
    def _validar_etiquetas(cls, v: list[str] | None) -> list[str] | None:
        return _limpiar_etiquetas(v)

    @model_validator(mode="after")
    def _al_menos_un_campo(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("Debes enviar al menos un campo para actualizar")
        return self


class EstadoUpdate(BaseModel):
    """Cambio de estado (para el Kanban)."""

    model_config = ConfigDict(extra="forbid")

    estado: EstadoTarea


class TareaOut(BaseModel):
    """Respuesta pública de una tarea."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    descripcion: str | None
    estado: EstadoTarea
    prioridad: PrioridadTarea
    fecha_vencimiento: datetime | None
    etiquetas: list[str]
    completado_en: datetime | None
    creado_en: str
    actualizado_en: str
