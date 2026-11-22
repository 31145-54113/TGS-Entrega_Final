"""Excepciones de dominio (no HTTP).

Los servicios lanzan estas; los routers las traducen a códigos HTTP.
Así la lógica de negocio no depende de FastAPI.
"""


class ErrorDominio(Exception):
    """Base de los errores de negocio."""


class EmailDuplicado(ErrorDominio):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"El correo '{email}' ya está registrado")


class CredencialesInvalidas(ErrorDominio):
    def __init__(self) -> None:
        super().__init__("Correo o contraseña incorrectos")

class NoEncontrado(ErrorDominio):
    """Recurso inexistente o no accesible para el usuario."""

    def __init__(self, recurso: str, id_: object) -> None:
        self.recurso = recurso
        self.id = id_
        super().__init__(f"{recurso} con id '{id_}' no encontrado")
