# Gestión de Tareas Académicas — App Web completa

Aplicación web **full-stack** para la gestión de tareas y trabajos en
entornos académicos, desarrollada como proyecto final de la cátedra
**Teoría General de Sistemas** (sección N-711) de la Escuela de Informática
de la Universidad Rafael Belloso Chacín (URBE).

Permite a estudiantes universitarios centralizar sus asignaciones,
organizarlas visualmente (lista + Kanban), monitorear su productividad
mediante un dashboard analítico y recibir avisos de tareas próximas a vencer.

---

## Stack

| Capa | Tecnología |
|---|---|
| **Backend** | FastAPI + Uvicorn |
| **Base de datos** | SQLite embebida (stdlib `sqlite3`) |
| **Autenticación** | JWT (HS256) vía PyJWT |
| **Hash de contraseñas** | PBKDF2-HMAC-SHA256 (600k iteraciones, salt 16 B) |
| **Validación** | Pydantic v2 |
| **Frontend** | HTML5 + CSS3 + Vanilla JS (ES Modules) |
| **Gráficos** | Chart.js 4 (CDN, sin build) |
| **Testing** | pytest + httpx |
| **Gestor de dependencias** | uv |
| **Python** | ≥ 3.11 |

**Decisiones de diseño:**

- **Sin ORM.** SQL puro sobre `sqlite3` para mostrar explícitamente el modelo
  Entidad-Relación del proyecto y mantener la trazabilidad.
- **Sin servidor de base de datos.** SQLite embebida: ideal para un proyecto
  académico, cero instalación, cero configuración.
- **Sin build step en el frontend.** HTML + CSS + JS servidos tal cual por
  FastAPI. Cero `npm install`, cero bundler, cero `node_modules`. Los módulos
  ES6 los resuelve el navegador.
- **SQLite multihilo.** La conexión se abre con `check_same_thread=False`
  porque FastAPI resuelve las dependencias y el endpoint en hilos distintos
  del threadpool. Cada request abre su propia conexión — no hay concurrencia
  real sobre un mismo objeto.
- **Arquitectura en capas.** Cada responsabilidad en su módulo:
  `api/` (HTTP) → `services/` (negocio) → `repositories/` (SQL) → `db/` (conexión).
  El frontend replica la idea: `api.js` centraliza HTTP, cada vista tiene su
  propio módulo.

---

## Requisitos

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** instalado (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

---

## Instalación y ejecución

```bash
# 1. Instalar dependencias (crea .venv automáticamente)
uv sync

# 2. Arrancar el servidor en modo desarrollo (con recarga)
uv run uvicorn app.main:app --reload
