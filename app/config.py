"""Configuración central de la aplicación.

Lee variables de entorno con valores por defecto para desarrollo local.
En producción, todas deberían venir del entorno (nunca del código).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    app_name: str = "Gestión de Tareas Académicas API"
    app_version: str = "0.1.0"
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "true").lower() == "true")

    # Base de datos SQLite embebida
    db_path: Path = field(
        default_factory=lambda: Path(os.getenv("DB_PATH", str(BASE_DIR / "data" / "app.db")))
    )

    # Seguridad / JWT
    jwt_secret: str = field(
        default_factory=lambda: os.getenv("JWT_SECRET", "cambiar-esta-clave-en-produccion")
    )
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = field(
        default_factory=lambda: int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))
    )


settings = Settings()
