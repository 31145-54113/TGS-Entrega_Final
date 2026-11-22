"""Dependencias compartidas de FastAPI (autenticación, etc.)."""
from __future__ import annotations

import sqlite3

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.db.connection import get_connection
from app.models.usuario import Usuario
from app.repositories import usuario_repo
from app.security.tokens import TokenInvalido, decode_token, get_subject

_bearer = HTTPBearer(auto_error=False)


def _no_autorizado(motivo: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=motivo,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    conn: sqlite3.Connection = Depends(get_connection),
) -> Usuario:
    """Resuelve el usuario a partir del JWT. Lanza 401 si algo falla."""
    if credentials is None:
        raise _no_autorizado("Token de acceso ausente")

    try:
        payload = decode_token(credentials.credentials)
        usuario_id = get_subject(payload)
    except TokenInvalido as exc:
        raise _no_autorizado(f"Token inválido: {exc}") from exc

    usuario = usuario_repo.por_id(conn, usuario_id)
    if usuario is None:
        # El token es válido pero el usuario ya no existe
        raise _no_autorizado("Usuario no encontrado")

    return usuario
