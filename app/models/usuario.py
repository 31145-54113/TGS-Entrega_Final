"""Modelo de dominio del usuario."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Usuario:
    """Usuario sin datos sensibles. Es lo que circula por la app."""
    id: int
    nombre: str
    email: str
    creado_en: str


@dataclass(frozen=True)
class CredencialesUsuario:
    """Usuario + hash de contraseña.

    Existe como tipo aparte para que el hash NO viaje fuera del flujo
    de autenticación. `repr=False` evita que se filtre en logs.
    """
    usuario: Usuario
    password_hash: str = field(repr=False)
