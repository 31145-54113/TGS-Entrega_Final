"""Acceso a datos de usuarios (SQL puro sobre SQLite)."""
from __future__ import annotations

import sqlite3

from app.exceptions import EmailDuplicado
from app.models.usuario import CredencialesUsuario, Usuario


def _fila_a_usuario(row: sqlite3.Row) -> Usuario:
    return Usuario(
        id=row["id"],
        nombre=row["nombre"],
        email=row["email"],
        creado_en=row["creado_en"],
    )


def crear(conn: sqlite3.Connection, nombre: str, email: str, password_hash: str) -> Usuario:
    """Inserta un usuario. Lanza EmailDuplicado si el correo ya existe."""
    try:
        row = conn.execute(
            """
            INSERT INTO usuarios (nombre, email, password_hash)
            VALUES (?, ?, ?)
            RETURNING id, nombre, email, creado_en
            """,
            (nombre, email, password_hash),
        ).fetchone()
    except sqlite3.IntegrityError as exc:
        raise EmailDuplicado(email) from exc
    return _fila_a_usuario(row)


def por_id(conn: sqlite3.Connection, usuario_id: int) -> Usuario | None:
    row = conn.execute(
        "SELECT id, nombre, email, creado_en FROM usuarios WHERE id = ?",
        (usuario_id,),
    ).fetchone()
    return _fila_a_usuario(row) if row else None


def credenciales_por_email(conn: sqlite3.Connection, email: str) -> CredencialesUsuario | None:
    """Devuelve el usuario + su hash (solo para el flujo de login)."""
    row = conn.execute(
        """
        SELECT id, nombre, email, creado_en, password_hash
        FROM usuarios
        WHERE email = ?
        """,
        (email,),
    ).fetchone()
    if row is None:
        return None
    return CredencialesUsuario(
        usuario=_fila_a_usuario(row),
        password_hash=row["password_hash"],
    )
