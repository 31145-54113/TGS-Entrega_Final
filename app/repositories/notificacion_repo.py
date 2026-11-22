"""Consultas de tareas con aviso de vencimiento (solo lectura)."""
from __future__ import annotations

import sqlite3

# Ventana de notificación: de hoy hacia atrás `dias_atras` días, y hacia
# adelante hasta +7 días. Las tareas vencidas hace mucho se ignoran para
# no saturar la vista con pendientes "abandonados".
_SQL_BASE = """
    SELECT
        id,
        titulo,
        estado,
        prioridad,
        fecha_vencimiento,
        CAST(
            julianday(DATE(fecha_vencimiento)) - julianday(DATE('now'))
            AS INTEGER
        ) AS dias_restantes
    FROM tareas
    WHERE usuario_id = ?
      AND estado != 'completada'
      AND fecha_vencimiento IS NOT NULL
      AND DATE(fecha_vencimiento) >= DATE('now', ?)
      AND DATE(fecha_vencimiento) <= DATE('now', '+7 days')
    ORDER BY
        CASE
            WHEN DATE(fecha_vencimiento) <  DATE('now') THEN 0
            WHEN DATE(fecha_vencimiento) =  DATE('now') THEN 1
            WHEN DATE(fecha_vencimiento) =  DATE('now', '+1 day') THEN 2
            ELSE 3
        END ASC,
        fecha_vencimiento ASC,
        id ASC
"""


def tareas_con_aviso(
    conn: sqlite3.Connection,
    usuario_id: int,
    dias_atras: int = 30,
) -> list[sqlite3.Row]:
    """Tareas no completadas con fecha de vencimiento en la ventana."""
    return conn.execute(
        _SQL_BASE,
        (usuario_id, f"-{dias_atras} days"),
    ).fetchall()
