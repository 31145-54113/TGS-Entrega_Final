"""Conexión a la base de datos SQLite embebida.

SQLite no necesita servidor: el archivo .db vive junto al código.
Cada request abre su propia conexión (no se comparte entre requests),
pero se desactiva `check_same_thread` porque FastAPI resuelve las
dependencias y el endpoint en hilos distintos del threadpool: la
conexión debe poder viajar entre ellos. La concurrencia real está
descartada porque cada request tiene su propio objeto Connection.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.config import settings

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def _connect() -> sqlite3.Connection:
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row           # filas accesibles como dict
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    """Conexión con cierre garantizado (uso interno, scripts, tests)."""
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Crea el archivo .db y aplica el esquema si no existe."""
    with connection() as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


def get_connection() -> Iterator[sqlite3.Connection]:
    """Dependencia de FastAPI: entrega la conexión y la cierra al final."""
    with connection() as conn:
        yield conn
