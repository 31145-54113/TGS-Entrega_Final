"""Endpoints de autenticación."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.config import settings
from app.db.connection import get_connection
from app.exceptions import CredencialesInvalidas, EmailDuplicado
from app.models.usuario import Usuario
from app.schemas.auth import LoginIn, RegistroIn, TokenOut, UsuarioOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Autenticación"])


def _token_out(access_token: str) -> TokenOut:
    return TokenOut(
        access_token=access_token,
        expires_in=settings.jwt_expiration_minutes * 60,
    )


@router.post("/registro", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def registro(datos: RegistroIn, conn: sqlite3.Connection = Depends(get_connection)) -> TokenOut:
    try:
        _, token = auth_service.registrar_usuario(
            conn, datos.nombre, str(datos.email), datos.password
        )
    except EmailDuplicado as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _token_out(token)


@router.post("/login", response_model=TokenOut)
def login(datos: LoginIn, conn: sqlite3.Connection = Depends(get_connection)) -> TokenOut:
    try:
        _, token = auth_service.autenticar_usuario(
            conn, str(datos.email), datos.password
        )
    except CredencialesInvalidas as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return _token_out(token)


@router.get("/me", response_model=UsuarioOut)
def me(usuario: Usuario = Depends(get_current_user)) -> UsuarioOut:
    """Devuelve el usuario autenticado. Requiere Bearer token."""
    return UsuarioOut.model_validate(usuario)
