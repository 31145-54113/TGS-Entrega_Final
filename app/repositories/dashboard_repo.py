"""Consultas analíticas sobre tareas (solo lectura)."""
from __future__ import annotations

import sqlite3


def total_tareas(conn: sqlite3.Connection, usuario_id: int) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM tareas WHERE usuario_id = ?", (usuario_id,)
    ).fetchone()[0]


def por_estado(conn: sqlite3.Connection, usuario_id: int) -> dict[str, int]:
    filas = conn.execute(
        "SELECT estado, COUNT(*) AS n FROM tareas WHERE usuario_id = ? GROUP BY estado",
        (usuario_id,),
    ).fetchall()
    return {r["estado"]: r["n"] for r in filas}


def por_prioridad(conn: sqlite3.Connection, usuario_id: int) -> dict[str, int]:
    filas = conn.execute(
        "SELECT prioridad, COUNT(*) AS n FROM tareas WHERE usuario_id = ? GROUP BY prioridad",
        (usuario_id,),
    ).fetchall()
    return {r["prioridad"]: r["n"] for r in filas}


def vencidas_pendientes(conn: sqlite3.Connection, usuario_id: int) -> int:
    return conn.execute(
        """
        SELECT COUNT(*) FROM tareas
        WHERE usuario_id = ?
          AND fecha_vencimiento IS NOT NULL
          AND fecha_vencimiento < datetime('now')
          AND estado != 'completada'
        """,
        (usuario_id,),
    ).fetchone()[0]


def proximas_dias(conn: sqlite3.Connection, usuario_id: int, dias: int) -> int:
    return conn.execute(
        """
        SELECT COUNT(*) FROM tareas
        WHERE usuario_id = ?
          AND fecha_vencimiento IS NOT NULL
          AND fecha_vencimiento >= datetime('now')
          AND fecha_vencimiento <= datetime('now', ?)
          AND estado != 'completada'
        """,
        (usuario_id, f"+{dias} days"),
    ).fetchone()[0]


def puntualidad(conn: sqlite3.Connection, usuario_id: int) -> tuple[int, int]:
    """Devuelve (completadas_con_fecha, a_tiempo)."""
    row = conn.execute(
        """
        SELECT
            COUNT(*) AS total,
            COALESCE(SUM(CASE WHEN completado_en <= fecha_vencimiento THEN 1 ELSE 0 END), 0) AS a_tiempo
        FROM tareas
        WHERE usuario_id = ?
          AND estado = 'completada'
          AND fecha_vencimiento IS NOT NULL
          AND completado_en IS NOT NULL
        """,
        (usuario_id,),
    ).fetchone()
    return row["total"], row["a_tiempo"]


def completadas_entre(
    conn: sqlite3.Connection,
    usuario_id: int,
    desde_sql: str,
    hasta_sql: str | None = None,
) -> int:
    """Cuenta tareas completadas en el rango [desde, hasta)."""
    if hasta_sql is None:
        sql = (
            "SELECT COUNT(*) FROM tareas "
            "WHERE usuario_id = ? AND estado = 'completada' "
            "AND completado_en >= datetime('now', ?)"
        )
        params = (usuario_id, desde_sql)
    else:
        sql = (
            "SELECT COUNT(*) FROM tareas "
            "WHERE usuario_id = ? AND estado = 'completada' "
            "AND completado_en >= datetime('now', ?) "
            "AND completado_en <  datetime('now', ?)"
        )
        params = (usuario_id, desde_sql, hasta_sql)
    return conn.execute(sql, params).fetchone()[0]


def completadas_por_dia(conn: sqlite3.Connection, usuario_id: int, dias: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT DATE(completado_en) AS dia, COUNT(*) AS n
        FROM tareas
        WHERE usuario_id = ?
          AND estado = 'completada'
          AND completado_en IS NOT NULL
          AND completado_en >= datetime('now', ?)
        GROUP BY DATE(completado_en)
        ORDER BY dia
        """,
        (usuario_id, f"-{dias - 1} days"),
    ).fetchall()


def tiempos_completado_horas(conn: sqlite3.Connection, usuario_id: int) -> list[float]:
    """Lista de tiempos (horas) desde creación hasta completado."""
    filas = conn.execute(
        """
        SELECT (julianday(completado_en) - julianday(creado_en)) * 24 AS horas
        FROM tareas
        WHERE usuario_id = ?
          AND estado = 'completada'
          AND completado_en IS NOT NULL
        """,
        (usuario_id,),
    ).fetchall()
    return [r["horas"] for r in filas if r["horas"] is not None]
