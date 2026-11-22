
## Orden de implementación que propongo (para que lo apruebes)

1. ✅ **Bloque 0 — Esqueleto + servidor + DB** (este mensaje).
2. ✅ **Bloque 1 — Seguridad**: `security/passwords.py` (hash/verify con pbkdf2) y `security/tokens.py` (crear/decodificar JWT).
3. ✅ **Bloque 2 — Auth**: `models/usuario.py`, `schemas/auth.py`, `repositories/usuario_repo.py`, `services/auth_service.py`, `api/routes/auth.py` (`POST /auth/registro`, `POST /auth/login`, `GET /auth/me`) + `api/dependencies.py` con `get_current_user`.
4. ✅ **Bloque 3 — Tareas**: CRUD completo, filtros, orden multicriterio y cambio de estado (lo que alimentará lista y Kanban).
5. ✅ **Bloque 4 — Dashboard**: endpoint de métricas (puntualidad, tasa semanal de completadas, distribución por prioridad).
6. ✅ **Bloque 5 — Notificaciones**: endpoint de tareas próximas a vencer.
7. **Bloque 6 — Tests** unitarios e integración con `pytest` + `httpx`.

¿Le damos con el **Bloque 1 (seguridad)** o prefieres ajustar algo antes — nombres de tablas, campos de `tareas`, puerto, etc.?
