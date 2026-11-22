"""Lógica de negocio de autenticación."""
from __future__ import annotations

import sqlite3

from app.exceptions import CredencialesInvalidas
from app.models.usuario import Usuario
from app.repositories import usuario_repo
from app.security.passwords import hash_password, verify_password
from app.security.tokens import create_access_token

# Hash "dummy" para igualar tiempos cuando el email no existe.
# Evita que un atacante deduzca si un correo está registrado midiendo
# el tiempo de respuesta del login (timing attack).
_HASH_FICTICIO = hash_password("password-ficticia-para-igualar-tiempos")


def registrar_usuario(conn: sqlite3.Connection, nombre: str, email: str, password: str) -> tuple[Usuario, str]:
    """Crea la cuenta y devuelve (usuario, token)."""
    password_hash = hash_password(password)
    usuario = usuario_repo.crear(conn, nombre, email, password_hash)
    token = create_access_token(usuario.id)
    return usuario, token


def autenticar_usuario(conn: sqlite3.Connection, email: str, password: str) -> tuple[Usuario, str]:
    """Valida credenciales y devuelve (usuario, token)."""
    credenciales = usuario_repo.credenciales_por_email(conn, email)

    if credenciales is None:
        # Consumir el mismo tiempo que un login real, sin revelar el motivo
        verify_password(password, _HASH_FICTICIO)
        raise CredencialesInvalidas()

    if not verify_password(password, credenciales.password_hash):
        raise CredencialesInvalidas()

    token = create_access_token(credenciales.usuario.id)
    return credenciales.usuario, token
