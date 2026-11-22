# API Backend — Bloques 5 y 6 (Notificaciones + Tests)

**Versión del documento:** 0.3
**Versión del backend:** 0.1.0
**Complementa a:**
- `API_Backend_v0.1.md` (autenticación)
- `API_Backend_v0.2_tareas_dashboard.md` (tareas + dashboard)

**Cátedra:** Teoría General de Sistemas · Sección N-711 · URBE

> Este documento describe los **endpoints de notificaciones** (Bloque 5)
> y la **suite de pruebas automatizadas** (Bloque 6). Con esto queda
> cerrado el alcance funcional del backend.

---

## 1. Convenciones heredadas

- **Base URL:** `http://127.0.0.1:8000`
- **Auth:** `Authorization: Bearer <token>` en todas las rutas marcadas 🔒.
- **Errores de negocio:** `{"detail": "<mensaje>"}`
- **Errores de validación:** 422 con lista de errores por campo.
- **Fechas en JSON:** ISO 8601 con zona UTC.

---

## 2. Endpoints de Notificaciones

### 2.1 Concepto

Una **notificación** es un aviso derivado del estado de las tareas:
no es una entidad propia en la base de datos. Se calcula al vuelo
filtrando las tareas del usuario que **vencen pronto o ya vencieron**.

**Reglas de clasificación por urgencia:**

| Urgencia | Condición | `dias_restantes` |
|---|---|---|
| `vencida` | `fecha_vencimiento < hoy` | negativo |
| `hoy` | vence hoy | 0 |
| `manana` | vence mañana | 1 |
| `esta_semana` | vence entre pasado mañana y +7 días | 2 a 7 |

**Reglas de inclusión/exclusión:**

- ✅ Tareas **no completadas** (`estado != 'completada'`)
- ✅ Tareas **con fecha de vencimiento**
- ✅ Vencidas en los últimos **30 días** (configurable con `?dias_atras=`)
- ✅ Hasta **+7 días** hacia el futuro
- ❌ Tareas completadas (ya no requieren acción)
- ❌ Tareas sin fecha límite
- ❌ Vencidas hace más de 30 días (para no saturar con pendientes abandonados)

> Las notificaciones **desaparecen automáticamente** cuando la tarea se
> completa: no hay que marcar nada. El aviso es una proyección del estado
> de la tarea, no un objeto persistente.

### 2.2 Tabla resumen

| Método | Ruta | Descripción | Códigos |
|---|---|---|---|
| `GET` | `/notificaciones` | Lista agrupada por urgencia | 200, 401, 422 |
| `GET` | `/notificaciones/conteo` | Solo conteos (para badge) | 200, 401, 422 |

---

### 2.3 `GET /notificaciones` — Listar notificaciones 🔒

**Uso:** alimenta la vista principal de notificaciones del frontend.

**Query params:**

| Parámetro | Tipo | Default | Rango | Descripción |
|---|---|---|---|---|
| `dias_atras` | int | 30 | 0–365 | Cuántos días hacia atrás mirar para tareas vencidas |

**Response `200 OK` (`NotificacionesOut`):**

```json
{
  "total": 4,
  "por_urgencia": {
    "vencida": 1,
    "hoy": 1,
    "manana": 1,
    "esta_semana": 1
  },
  "notificaciones": [
    {
      "tarea_id": 1,
      "titulo": "Tarea vencida",
      "estado": "pendiente",
      "prioridad": "alta",
      "fecha_vencimiento": "2026-11-21T10:00:00Z",
      "urgencia": "vencida",
      "dias_restantes": -1
    },
    {
      "tarea_id": 2,
      "titulo": "Vence hoy",
      "estado": "pendiente",
      "prioridad": "critica",
      "fecha_vencimiento": "2026-11-22T23:59:00Z",
      "urgencia": "hoy",
      "dias_restantes": 0
    }
  ]
}
```

**Orden de los elementos:** primero por urgencia (vencida → hoy → mañana → esta semana), luego por `fecha_vencimiento` ascendente, y desempate por `id`.

**Errores:**

| Código | Cuándo |
|---|---|
| `401` | Token ausente o inválido |
| `422` | `dias_atras` fuera de rango (0–365) |

**Ejemplos:**

```bash
# Notificaciones estándar (30 días atrás)
curl http://127.0.0.1:8000/notificaciones -H "Authorization: Bearer $TOKEN"

# Ver más historia (90 días)
curl "http://127.0.0.1:8000/notificaciones?dias_atras=90" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 2.4 `GET /notificaciones/conteo` — Solo conteos 🔒

**Uso:** endpoint ligero para el **badge numérico** del header (evita
traer el array completo cuando solo se necesita el número rojo).

**Query params:** iguales a `GET /notificaciones` (`dias_atras`).

**Response `200 OK` (`ConteoNotificacionesOut`):**

```json
{
  "total": 4,
  "vencidas": 1,
  "hoy": 1,
  "manana": 1,
  "esta_semana": 1
}
```

**Ejemplo:**

```bash
curl http://127.0.0.1:8000/notificaciones/conteo \
  -H "Authorization: Bearer $TOKEN"
```

> Los nombres de los campos (`vencidas`, `hoy`, `manana`, `esta_semana`)
> están en plural y en español para calzar con el badge del frontend sin
> transformaciones.

---

## 3. Modelos de datos de Notificaciones

### 3.1 `NotificacionOut`

```typescript
{
  tarea_id:          number
  titulo:            string
  estado:            "pendiente" | "en_progreso" | "completada"
  prioridad:         "baja" | "media" | "alta" | "critica"
  fecha_vencimiento: string   // ISO 8601 UTC
  urgencia:          "vencida" | "hoy" | "manana" | "esta_semana"
  dias_restantes:    number   // negativo si vencida
}
```

### 3.2 `ConteoPorUrgencia`

```typescript
{ vencida: number; hoy: number; manana: number; esta_semana: number }
```

### 3.3 `NotificacionesOut`

```typescript
{
  total:          number
  por_urgencia:   ConteoPorUrgencia
  notificaciones: NotificacionOut[]
}
```

### 3.4 `ConteoNotificacionesOut`

```typescript
{
  total:        number
  vencidas:     number
  hoy:          number
  manana:       number
  esta_semana:  number
}
```

---

## 4. Suite de pruebas automatizadas

El backend incluye **52 tests** organizados por módulo. Se ejecutan en
~6 segundos y **no tocan `data/app.db`**: cada test corre contra una
base de datos SQLite temporal en `tmp_path`.

### 4.1 Cómo correr los tests

```bash
# Asegurar dependencias de desarrollo
uv sync --group dev

# Suite completa
uv run pytest -v

# Un archivo
uv run pytest tests/test_auth.py -v

# Un test específico
uv run pytest tests/test_tareas.py::test_listar_solo_propias -v

# Sin warnings
uv run pytest -v --disable-warnings
```

**Resultado esperado:** `52 passed`.

### 4.2 Estructura de la carpeta `tests/`

```
tests/
├── __init__.py
├── conftest.py               ← fixtures compartidas
├── test_passwords.py         ← 7 tests
├── test_tokens.py            ← 6 tests
├── test_auth.py              ← 12 tests
├── test_tareas.py            ← 16 tests
├── test_dashboard.py         ← 4 tests
└── test_notificaciones.py    ← 7 tests
```

### 4.3 Aislamiento de la base de datos

La fixture `db_aislada` en `conftest.py` redirige `settings.db_path`
a una ruta temporal **antes de cada test** y la restaura al terminar.
Esto garantiza que:

- `data/app.db` **nunca** se modifica al correr tests.
- Cada test arranca con una DB limpia (no hay contaminación entre tests).
- Los tests pueden correr en paralelo sin conflictos.

### 4.4 Fixtures disponibles en `conftest.py`

| Fixture | Qué entrega |
|---|---|
| `db_aislada` | Redirige `settings.db_path` a una DB temporal |
| `client` | `TestClient` de FastAPI con lifespan activo (crea tablas) |
| `usuario_data` | Dict con datos de un usuario de prueba |
| `token` | Token JWT de un usuario ya registrado |
| `auth` | Header `Authorization: Bearer <token>` listo para usar |
| `segundo_usuario` | Header de auth de un **segundo** usuario (para tests de aislamiento) |

### 4.5 Qué cubre cada archivo

#### `test_passwords.py` (7 tests)

- Formato autocontenido del hash (`pbkdf2_sha256$600000$...$...`)
- El hash **no** contiene la contraseña en claro
- Dos hashes del mismo password son distintos (salt aleatorio)
- Verificación correcta / incorrecta
- Hash corrupto devuelve `False` (no lanza)
- Rechaza password vacío

#### `test_tokens.py` (6 tests)

- Round-trip `create → decode`
- `sub` casteable a entero
- Token manipulado (último carácter cambiado) → `TokenInvalido`
- Token basura → `TokenInvalido`
- Token expirado → `TokenInvalido`
- Token sin `sub` → `TokenInvalido`

#### `test_auth.py` (12 tests)

- Registro exitoso devuelve token
- Email duplicado → `409`
- Email duplicado case-insensitive (`ANA@` vs `ana@`) → `409`
- Password corta → `422`
- Email inválido → `422`
- Campo extra → `422` (por `extra="forbid"`)
- Login exitoso
- Login con password mala → `401` con `WWW-Authenticate: Bearer`
- **Anti-enumeración:** login con email inexistente devuelve el mismo mensaje que password mala
- `/auth/me` sin token → `401`
- `/auth/me` con token basura → `401`
- `/auth/me` con token válido → datos del usuario, **sin** `password_hash`

#### `test_tareas.py` (16 tests)

- Crear tarea con todos los campos
- Crear sin auth → `401`
- Título vacío → `422`
- Etiquetas normalizadas (`  TGS  ` → `tgs`, deduplicadas)
- Etiquetas con caracteres prohibidos → `422`
- **Aislamiento:** un usuario no ve tareas de otro
- **Aislamiento:** `GET /tareas/{id}` de otro usuario → `404`
- PATCH parcial (solo cambia lo enviado)
- PATCH con `descripcion: null` limpia el campo
- PATCH sin ningún campo → `422`
- Cambio a `completada` setea `completado_en`
- Cambio desde `completada` limpia `completado_en`
- DELETE → `204` y posterior GET → `404`
- Filtro por estado + prioridad
- Orden por prioridad (`critica → alta → media → baja`, no alfabético)
- Filtro `vencidas=true`

#### `test_dashboard.py` (4 tests)

- Dashboard vacío: `tasa: null`, `variacion_pct: null`, `promedio_horas: null`, serie de 7 ceros
- Conteos correctos por estado y prioridad
- Puntualidad: una a tiempo + una tarde → `tasa: 50.0`
- Serie diaria siempre tiene 7 elementos

#### `test_notificaciones.py` (7 tests)

- Sin tareas → lista vacía
- Clasificación de las 4 urgencias (`vencida`, `hoy`, `manana`, `esta_semana`)
- Tareas a más de 7 días **no** aparecen
- Tareas completadas **no** aparecen
- Tareas sin fecha **no** aparecen
- Aislamiento entre usuarios
- `/notificaciones/conteo` consistente con `/notificaciones`

### 4.6 Configuración de pytest

En `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-q --strict-markers"
```

### 4.7 Warning conocido

```
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient`
is deprecated; install `httpx2` instead.
```

Viene de la librería, no de nuestro código. No afecta el funcionamiento.
Migrar a `httpx2` **ahora** rompe `TestClient` porque Starlette aún no lo
soporta oficialmente. Se silencia con `--disable-warnings` cuando moleste.

---

## 5. Estado final del backend

Tras los 6 bloques, el backend cubre el 100% del alcance funcional del PDF:

| Módulo del alcance | Endpoints | Tests |
|---|---|---|
| Autenticación | 3 | 12 + 13 (passwords + tokens) |
| Tareas (CRUD) | 6 | 16 |
| Dashboard | 1 | 4 |
| Notificaciones | 2 | 7 |
| **Total** | **12 endpoints** | **52 tests** |

**Exclusiones del alcance (por diseño del PDF):**

- Pasarelas de pago / suscripciones → ❌ no implementado
- Videoconferencia / multimedia → ❌ no implementado
- App nativa Android/iOS → ❌ fuera (solo web responsiva)

**Lo que no está en el alcance inicial pero podría sumarse después:**

- Rate limiting en `/auth/login` (para producción)
- Notificaciones push / email (el PDF pide "avisos en pantalla")
- Recordatorios personalizados por usuario (tabla `recordatorios`)
- Estado "leído/no leído" en notificaciones (hoy es stateless)
- Timezone por usuario (hoy todo en UTC)

---

## 6. Flujo completo end-to-end (referencia)

```bash
# 1. Registro
curl -X POST http://127.0.0.1:8000/auth/registro \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Ana","email":"ana@urbe.edu","password":"clave12345"}'

# 2. Guardar token
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ana@urbe.edu","password":"clave12345"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 3. Crear tarea con vencimiento mañana
curl -X POST http://127.0.0.1:8000/tareas \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"titulo":"Entrega TGS","fecha_vencimiento":"2026-11-23T23:59:00Z","prioridad":"alta"}'

# 4. Ver notificaciones (debe aparecer en "manana")
curl http://127.0.0.1:8000/notificaciones -H "Authorization: Bearer $TOKEN"

# 5. Completar la tarea
curl -X PATCH http://127.0.0.1:8000/tareas/1/estado \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"estado":"completada"}'

# 6. Verificar que desapareció de notificaciones
curl http://127.0.0.1:8000/notificaciones/conteo -H "Authorization: Bearer $TOKEN"

# 7. Ver dashboard (debe reflejar la completada)
curl http://127.0.0.1:8000/dashboard -H "Authorization: Bearer $TOKEN"
```

---

## 7. Índice de la documentación completa

| Documento | Contenido |
|---|---|
| `API_Backend_v0.1.md` | Autenticación: registro, login, `/auth/me`, seguridad, DB |
| `API_Backend_v0.2_tareas_dashboard.md` | Tareas CRUD, filtros, Kanban, dashboard analítico |
| `API_Backend_v0.3_notificaciones_tests.md` | **Este documento.** Notificaciones y suite de tests |
