"""Punto de entrada del backend.

Crea la aplicación FastAPI, inicializa la base de datos al arrancar y
monta los routers de la API. Para correr:

    uv run uvicorn app.main:app --reload
    # o bien
    uv run python -m app.main
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db.connection import init_db
from app.api.routes import auth as auth_routes
from app.api.routes import tareas as tareas_routes
from app.api.routes import dashboard as dashboard_routes
from app.api.routes import notificaciones as notificaciones_routes


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(tareas_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(notificaciones_routes.router)


# ─────────────────────────────────────────────────────────────
#  Frontend (SPA estática servida por la propia API)
# ─────────────────────────────────────────────────────────────
FRONTEND_DIR = Path(__file__).parent / "frontend"
if FRONTEND_DIR.is_dir():
    app.mount(
        "/app",
        StaticFiles(directory=FRONTEND_DIR, html=True),
        name="frontend",
    )


@app.get("/", tags=["Salud"])
def root() -> dict[str, str]:
    return {
        "servicio": settings.app_name,
        "version": settings.app_version,
        "estado": "ok",
    }


@app.get("/health", tags=["Salud"])
def health() -> dict[str, str]:
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=settings.debug,
    )
