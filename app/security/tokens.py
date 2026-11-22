"""Emisión y validación de JSON Web Tokens (JWT).

El token solo transporta la identidad del usuario (`sub` = id) y sus
metadatos de tiempo. Los permisos y datos sensibles NO viajan en el
token: se consultan a la base de datos en cada request protegido.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.config import settings

TOKEN_TYPE = "access"


class TokenInvalido(Exception):
    """Se lanza cuando un token está expirado, corrupto o mal firmado."""


def create_access_token(subject: int | str, expires_minutes: int | None = None) -> str:
    """Firma un JWT de acceso para el usuario indicado."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expires_minutes or settings.jwt_expiration_minutes)

    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": TOKEN_TYPE,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """Valida un JWT y devuelve su payload.

    Lanza TokenInvalido si la firma no cuadra, si está expirado o si el
    tipo de token no corresponde a uno de acceso.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "exp", "type"]},
        )
    except jwt.PyJWTError as exc:
        raise TokenInvalido(str(exc)) from exc

    if payload.get("type") != TOKEN_TYPE:
        raise TokenInvalido("Tipo de token no válido")

    return payload


def get_subject(payload: dict[str, Any]) -> int:
    """Extrae el `sub` del payload como entero.

    Centraliza el casteo para que los servicios no tengan que repetirlo.
    """
    try:
        return int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise TokenInvalido("Token sin 'sub' válido") from exc
