"""Acceso a datos de tareas (SQL puro sobre SQLite)."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from app.models.tarea import EstadoTarea, PrioridadTarea, Tarea

_FMT_DB = "%Y-%m-%d %H:%M:%S"

# Orden personalizado por prioridad (critica primero)
_ORDEN_PRIORIDAD = (
    "CASE prioridad "
    "WHEN 'critica' THEN 0 WHEN 'alta' THEN 1 "
    "WHEN 'media'   THEN 2 WHEN 'baja' THEN 3 END"
)
_CAMPOS_ORDEN = {
    "prioridad": _ORDEN_PRIORIDAD,
    "fecha_vencimiento": "fecha_vencimiento",
    "creado_en": "creado_en",
    "actualizado_en": "actualizado_en",
    "titulo": "titulo COLLATE NOCASE",
}


def _a_db(fecha: datetime | None) -> str | None:
    """datetime → string UTC en formato SQLite."""
    if fecha is None:
        return None
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=timezone.utc)
    return fecha.astimezone(timezone.utc).strftime(_FMT_DB)


def _desde_db(texto: str | None) -> datetime | None:
    if not texto:
        return None
    return datetime.strptime(texto, _FMT_DB).replace(tzinfo=timezone.utc)


def _tags_a_db(etiquetas: list[str]) -> str | None:
    return ",".join(etiquetas) if etiquetas else None


def _tags_desde_db(texto: str | None) -> list[str]:
    return [t for t in texto.split(",") if t] if texto else []


def _fila_a_tarea(row: sqlite3.Row) -> Tarea:
    return Tarea(
        id=row["id"],
        usuario_id=row["usuario_id"],
        titulo=row["titulo"],
        descripcion=row["descripcion"],
        estado=EstadoTarea(row["estado"]),
        prioridad=PrioridadTarea(row["prioridad"]),
        fecha_vencimiento=_desde_db(row["fecha_vencimiento"]),
        etiquetas=_tags_desde_db(row["etiquetas"]),
	completado_en=_desde_db(row["completado_en"]),
        creado_en=row["creado_en"],
        actualizado_en=row["actualizado_en"],
    )


def crear(
    conn: sqlite3.Connection,
    usuario_id: int,
    *,
    titulo: str,
    descripcion: str | None,
    estado: EstadoTarea,
    prioridad: PrioridadTarea,
    fecha_vencimiento: datetime | None,
    etiquetas: list[str],
    completado_en: datetime | None = None,
) -> Tarea:
    row = conn.execute(
        """
        INSERT INTO tareas
            (usuario_id, titulo, descripcion, estado, prioridad, fecha_vencimiento, etiquetas, completado_en)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        RETURNING *
        """,
        (
            usuario_id, titulo, descripcion, estado.value, prioridad.value,
            _a_db(fecha_vencimiento), _tags_a_db(etiquetas), _a_db(completado_en),
        ),
    ).fetchone()
    return _fila_a_tarea(row)


def por_id(conn: sqlite3.Connection, usuario_id: int, tarea_id: int) -> Tarea | None:
    row = conn.execute(
        "SELECT * FROM tareas WHERE id = ? AND usuario_id = ?",
        (tarea_id, usuario_id),
    ).fetchone()
    return _fila_a_tarea(row) if row else None


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
    sql = ["SELECT * FROM tareas WHERE usuario_id = ?"]
    params: list[object] = [usuario_id]

    if estado is not None:
        sql.append("AND estado = ?")
        params.append(estado.value)
    if prioridad is not None:
        sql.append("AND prioridad = ?")
        params.append(prioridad.value)
    if etiqueta:
        tag = etiqueta.strip().lower()
        sql.append("AND ',' || COALESCE(etiquetas, '') || ',' LIKE ?")
        params.append(f"%,{tag},%")
    if busqueda:
        like = f"%{busqueda.strip()}%"
        sql.append("AND (titulo LIKE ? OR COALESCE(descripcion, '') LIKE ?)")
        params.extend([like, like])
    if vencidas:
        sql.append(
            "AND fecha_vencimiento IS NOT NULL "
            "AND fecha_vencimiento < datetime('now') "
            "AND estado != 'completada'"
        )
    if proximas_dias is not None:
        if proximas_dias < 1:
            raise ValueError("proximas_dias debe ser >= 1")
        sql.append(
            "AND fecha_vencimiento IS NOT NULL "
            "AND fecha_vencimiento >= datetime('now') "
            "AND fecha_vencimiento <= datetime('now', ?) "
            "AND estado != 'completada'"
        )
        params.append(f"+{proximas_dias} days")

    expr = _CAMPOS_ORDEN.get(orden_por, _CAMPOS_ORDEN["creado_en"])
    direccion = "DESC" if orden.lower() == "desc" else "ASC"
    if orden_por == "fecha_vencimiento":
        sql.append(f"ORDER BY (fecha_vencimiento IS NULL) ASC, {expr} {direccion}, id ASC")
    else:
        sql.append(f"ORDER BY {expr} {direccion}, id ASC")

    return [_fila_a_tarea(r) for r in conn.execute(" ".join(sql), params).fetchall()]


def actualizar(
    conn: sqlite3.Connection,
    usuario_id: int,
    tarea_id: int,
    cambios: dict[str, object],
) -> Tarea | None:
    """Aplica `cambios` (ya validados por el service) y devuelve la tarea.

    Cada clave de `cambios` es un nombre de columna; el service garantiza
    que solo llegan columnas permitidas y con valores ya serializados.
    """
    if not cambios:
        return por_id(conn, usuario_id, tarea_id)

    set_sql = ", ".join(f"{col} = ?" for col in cambios)
    params = list(cambios.values()) + [tarea_id, usuario_id]
    row = conn.execute(
        f"UPDATE tareas SET {set_sql}, actualizado_en = datetime('now') "
        "WHERE id = ? AND usuario_id = ? RETURNING *",
        params,
    ).fetchone()
    return _fila_a_tarea(row) if row else None


def eliminar(conn: sqlite3.Connection, usuario_id: int, tarea_id: int) -> bool:
    cur = conn.execute(
        "DELETE FROM tareas WHERE id = ? AND usuario_id = ?",
        (tarea_id, usuario_id),
    )
    return cur.rowcount > 0
