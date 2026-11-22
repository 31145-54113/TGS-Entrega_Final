"""Lógica de negocio de tareas."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

from app.exceptions import NoEncontrado
from app.models.tarea import EstadoTarea, PrioridadTarea, Tarea
from app.repositories import tarea_repo
from app.schemas.tarea import TareaCreate, TareaUpdate

_COLUMNAS_ACTUALIZABLES = {
    "titulo", "descripcion", "estado", "prioridad",
    "fecha_vencimiento", "etiquetas",
}

_FMT_DB = "%Y-%m-%d %H:%M:%S"


def _ahora_db() -> str:
    return datetime.now(timezone.utc).strftime(_FMT_DB)


def _marcar_completado(
    cambios: dict[str, object],
    estado_anterior: EstadoTarea,
    estado_nuevo: EstadoTarea,
) -> None:
    """Ajusta `completado_en` según la transición de estado."""
    if estado_nuevo == EstadoTarea.COMPLETADA and estado_anterior != EstadoTarea.COMPLETADA:
        cambios["completado_en"] = _ahora_db()
    elif estado_nuevo != EstadoTarea.COMPLETADA and estado_anterior == EstadoTarea.COMPLETADA:
        cambios["completado_en"] = None


def crear(conn: sqlite3.Connection, usuario_id: int, datos: TareaCreate) -> Tarea:
    completado_en = (
        datetime.now(timezone.utc) if datos.estado == EstadoTarea.COMPLETADA else None
    )
    return tarea_repo.crear(
        conn,
        usuario_id,
        titulo=datos.titulo,
        descripcion=datos.descripcion,
        estado=datos.estado,
        prioridad=datos.prioridad,
        fecha_vencimiento=datos.fecha_vencimiento,
        etiquetas=datos.etiquetas,
        completado_en=completado_en,
    )


def listar(
    conn: sqlite3.Connection,
    usuario_id: int,
    *,
    estado: EstadoTarea | None = None,
    prioridad: PrioridadTarea | None = None,
    etiqueta: str | None = None,
    busqueda: str | None = None,
    vencidas: bool = False,
    proximas_dias: int | None = None,
    orden_por: str = "fecha_vencimiento",
    orden: str = "asc",
) -> list[Tarea]:
    return tarea_repo.listar(
        conn, usuario_id,
        estado=estado, prioridad=prioridad, etiqueta=etiqueta,
        busqueda=busqueda, vencidas=vencidas, proximas_dias=proximas_dias,
        orden_por=orden_por, orden=orden,
    )


def obtener(conn: sqlite3.Connection, usuario_id: int, tarea_id: int) -> Tarea:
    tarea = tarea_repo.por_id(conn, usuario_id, tarea_id)
    if tarea is None:
        raise NoEncontrado("Tarea", tarea_id)
    return tarea


def actualizar(
    conn: sqlite3.Connection,
    usuario_id: int,
    tarea_id: int,
    datos: TareaUpdate,
) -> Tarea:
    tarea_actual = tarea_repo.por_id(conn, usuario_id, tarea_id)
    if tarea_actual is None:
        raise NoEncontrado("Tarea", tarea_id)

    enviados: dict[str, Any] = datos.model_dump(exclude_unset=True)
    cambios: dict[str, object] = {}

    for campo, valor in enviados.items():
        if campo not in _COLUMNAS_ACTUALIZABLES:
            continue
        if campo == "estado" and valor is not None:
            cambios["estado"] = valor.value
            _marcar_completado(cambios, tarea_actual.estado, valor)
        elif campo == "prioridad" and valor is not None:
            cambios["prioridad"] = valor.value
        elif campo == "fecha_vencimiento":
            cambios["fecha_vencimiento"] = tarea_repo._a_db(valor)
        elif campo == "etiquetas":
            cambios["etiquetas"] = tarea_repo._tags_a_db(valor or [])
        else:
            cambios[campo] = valor

    actualizada = tarea_repo.actualizar(conn, usuario_id, tarea_id, cambios)
    if actualizada is None:
        raise NoEncontrado("Tarea", tarea_id)
    return actualizada


def cambiar_estado(
    conn: sqlite3.Connection,
    usuario_id: int,
    tarea_id: int,
    nuevo_estado: EstadoTarea,
) -> Tarea:
    tarea_actual = tarea_repo.por_id(conn, usuario_id, tarea_id)
    if tarea_actual is None:
        raise NoEncontrado("Tarea", tarea_id)

    cambios: dict[str, object] = {"estado": nuevo_estado.value}
    _marcar_completado(cambios, tarea_actual.estado, nuevo_estado)

    actualizada = tarea_repo.actualizar(conn, usuario_id, tarea_id, cambios)
    if actualizada is None:
        raise NoEncontrado("Tarea", tarea_id)
    return actualizada


def eliminar(conn: sqlite3.Connection, usuario_id: int, tarea_id: int) -> None:
    if not tarea_repo.eliminar(conn, usuario_id, tarea_id):
        raise NoEncontrado("Tarea", tarea_id)
