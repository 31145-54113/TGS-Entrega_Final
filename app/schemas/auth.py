"""Schemas Pydantic para los endpoints de autenticación."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegistroIn(BaseModel):
    """Datos para crear una cuenta."""

    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("nombre", mode="before")
    @classmethod
    def _limpiar_nombre(cls, v: object) -> object:
        return v.strip() if isinstance(v, str) else v

    @field_validator("email", mode="before")
    @classmethod
    def _normalizar_email(cls, v: object) -> object:
        return v.strip().lower() if isinstance(v, str) else v

    @field_validator("password")
    @classmethod
    def _password_no_vacia(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("La contraseña no puede ser solo espacios")
        return v


class LoginIn(BaseModel):
    """Credenciales para iniciar sesión."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def _normalizar_email(cls, v: object) -> object:
        return v.strip().lower() if isinstance(v, str) else v


class UsuarioOut(BaseModel):
    """Representación pública del usuario (sin hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: EmailStr
    creado_en: str


class TokenOut(BaseModel):
    """Respuesta estándar de login/registro."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int   # segundos
