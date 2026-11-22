"""Endpoints de tareas (todas las rutas requieren autenticación)."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_current_user
from app.db.connection import get_connection
from app.exceptions import NoEncontrado
from app.models.tarea import EstadoTarea, PrioridadTarea
from app.models.usuario import Usuario
from app.schemas.tarea import EstadoUpdate, TareaCreate, TareaOut, TareaUpdate
from app.services import tarea_service

router = APIRouter(prefix="/tareas", tags=["Tareas"])


def _404(exc: NoEncontrado) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("", response_model=list[TareaOut])
def listar_tareas(
    estado: EstadoTarea | None = None,
    prioridad: PrioridadTarea | None = None,
    etiqueta: str | None = Query(default=None, max_length=30),
    busqueda: str | None = Query(default=None, max_length=200),
    vencidas: bool = False,
    proximas_dias: int | None = Query(default=None, ge=1, le=365),
    orden_por: str = Query(default="fecha_vencimiento",
                           pattern="^(prioridad|fecha_vencimiento|creado_en|actualizado_en|titulo)$"),
    orden: str = Query(default="asc", pattern="^(asc|desc)$"),
    usuario: Usuario = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_connection),
) -> list[TareaOut]:
    """Lista las tareas del usuario con filtros y ordenamiento."""
    tareas = tarea_service.listar(
        conn, usuario.id,
        estado=estado, prioridad=prioridad, etiqueta=etiqueta, busqueda=busqueda,
        vencidas=vencidas, proximas_dias=proximas_dias,
        orden_por=orden_por, orden=orden,
    )
    return [TareaOut.model_validate(t) for t in tareas]


@router.post("", response_model=TareaOut, status_code=status.HTTP_201_CREATED)
def crear_tarea(
    datos: TareaCreate,
    usuario: Usuario = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_connection),
) -> TareaOut:
    tarea = tarea_service.crear(conn, usuario.id, datos)
    return TareaOut.model_validate(tarea)


@router.get("/{tarea_id}", response_model=TareaOut)
def obtener_tarea(
    tarea_id: int,
    usuario: Usuario = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_connection),
) -> TareaOut:
    try:
        tarea = tarea_service.obtener(conn, usuario.id, tarea_id)
    except NoEncontrado as exc:
        raise _404(exc) from exc
    return TareaOut.model_validate(tarea)


@router.patch("/{tarea_id}", response_model=TareaOut)
def actualizar_tarea(
    tarea_id: int,
    datos: TareaUpdate,
    usuario: Usuario = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_connection),
) -> TareaOut:
    try:
        tarea = tarea_service.actualizar(conn, usuario.id, tarea_id, datos)
    except NoEncontrado as exc:
        raise _404(exc) from exc
    return TareaOut.model_validate(tarea)


@router.patch("/{tarea_id}/estado", response_model=TareaOut)
def cambiar_estado_tarea(
    tarea_id: int,
    datos: EstadoUpdate,
    usuario: Usuario = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_connection),
) -> TareaOut:
    """Endpoint específico para el drag & drop del Kanban."""
    try:
        tarea = tarea_service.cambiar_estado(conn, usuario.id, tarea_id, datos.estado)
    except NoEncontrado as exc:
        raise _404(exc) from exc
    return TareaOut.model_validate(tarea)


@router.delete("/{tarea_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_tarea(
    tarea_id: int,
    usuario: Usuario = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_connection),
) -> None:
    try:
        tarea_service.eliminar(conn, usuario.id, tarea_id)
    except NoEncontrado as exc:
        raise _404(exc) from exc
