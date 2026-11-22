# API Backend — Aplicación Web de Gestión de Tareas Académicas

**Versión del documento:** 0.1
**Versión del backend:** 0.1.0
**Última actualización:** Bloque 2 (Autenticación completa)
**Cátedra:** Teoría General de Sistemas · Sección N-711 · URBE

---

## 1. Información general

| Campo | Valor |
|---|---|
| **Base URL (desarrollo)** | `http://127.0.0.1:8000` |
| **Documentación interactiva (Swagger)** | `http://127.0.0.1:8000/docs` |
| **Documentación alternativa (ReDoc)** | `http://127.0.0.1:8000/redoc` |
| **Formato de intercambio** | JSON (`application/json`) |
| **Codificación** | UTF-8 |
| **Autenticación** | JWT (Bearer token) |
| **Base de datos** | SQLite embebida (`data/app.db`) |

### 1.1 Convenciones de respuesta

**Errores de negocio y de autenticación** → objeto con un solo campo `detail`:

```json
{ "detail": "El correo 'ana@urbe.edu' ya está registrado" }
```

**Errores de validación (422)** → lista de errores por campo:

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "nombre"],
      "msg": "String should have at least 2 characters",
      "input": "A"
    }
  ]
}
```

**Respuestas exitosas** → el schema del endpoint (sección 4).

### 1.2 Autenticación

Los endpoints marcados con 🔒 requieren la cabecera:

```
Authorization: Bearer <access_token>
```

- El token se obtiene en `POST /auth/registro` o `POST /auth/login`.
- **Vigencia:** 60 minutos (configurable con `JWT_EXPIRATION_MINUTES`).
- **Tipo:** `Bearer` (HS256).
- **Payload del token** (JWT decodificado, solo a modo informativo):

```json
{
  "sub": "1",
  "iat": 1735689600,
  "exp": 1735693200,
  "type": "access"
}
```

> `sub` es el ID del usuario como string; el backend lo castea a entero.

---

## 2. Endpoints disponibles

| Método | Ruta | Descripción | Auth | Códigos |
|---|---|---|---|---|
| `GET` | `/` | Info del servicio | No | 200 |
| `GET` | `/health` | Health check | No | 200 |
| `POST` | `/auth/registro` | Crear cuenta + emitir token | No | 201, 409, 422 |
| `POST` | `/auth/login` | Autenticarse + emitir token | No | 200, 401, 422 |
| `GET` | `/auth/me` | Datos del usuario autenticado | 🔒 | 200, 401 |

---

## 3. Detalle de cada endpoint

### 3.1 `GET /` — Info del servicio

**Uso:** sanity check rápido de que el servidor responde.

**Request:** sin body.

**Response `200 OK`:**

```json
{
  "servicio": "Gestión de Tareas Académicas API",
  "version": "0.1.0",
  "estado": "ok"
}
```

**Ejemplo:**

```bash
curl http://127.0.0.1:8000/
```

---

### 3.2 `GET /health` — Health check

**Uso:** ideal para monitoreo (Docker healthchecks, uptime probes).

**Request:** sin body.

**Response `200 OK`:**

```json
{ "status": "healthy" }
```

**Ejemplo:**

```bash
curl http://127.0.0.1:8000/health
```

---

### 3.3 `POST /auth/registro` — Registro de usuario

**Uso:** crea una cuenta nueva y devuelve un token listo para usar. El usuario no necesita hacer login después.

**Request body:**

| Campo | Tipo | Obligatorio | Restricciones |
|---|---|---|---|
| `nombre` | string | Sí | 2–100 caracteres. Se limpia con `.strip()`. |
| `email` | string (email) | Sí | Formato de correo válido. Se normaliza a minúsculas. Único en la DB (case-insensitive). |
| `password` | string | Sí | 8–128 caracteres. No puede ser solo espacios. |

**Ejemplo de request:**

```json
{
  "nombre": "Ana Pérez",
  "email": "ana@urbe.edu",
  "password": "clave12345"
}
```

**Response `201 Created`:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Errores:**

| Código | Cuándo | Body |
|---|---|---|
| `409 Conflict` | El correo ya está registrado | `{"detail": "El correo 'ana@urbe.edu' ya está registrado"}` |
| `422 Unprocessable Entity` | Nombre corto, email inválido, password corta, campo extra (`extra="forbid"`) | Lista de errores por campo |

**Ejemplo:**

```bash
curl -X POST http://127.0.0.1:8000/auth/registro \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Ana Pérez","email":"ana@urbe.edu","password":"clave12345"}'
```

---

### 3.4 `POST /auth/login` — Inicio de sesión

**Uso:** valida credenciales y emite un nuevo token.

**Request body:**

| Campo | Tipo | Obligatorio | Restricciones |
|---|---|---|---|
| `email` | string (email) | Sí | Formato válido. Se normaliza a minúsculas. |
| `password` | string | Sí | 1–128 caracteres. |

**Ejemplo de request:**

```json
{
  "email": "ana@urbe.edu",
  "password": "clave12345"
}
```

**Response `200 OK`:** idéntica a `POST /auth/registro` (`TokenOut`).

**Errores:**

| Código | Cuándo | Body |
|---|---|---|
| `401 Unauthorized` | Email no existe **o** contraseña incorrecta (el backend no distingue el motivo — anti enumeración de correos) | `{"detail": "Correo o contraseña incorrectos"}` |
| `422 Unprocessable Entity` | Validación de campos | Lista de errores |

**Headers de error 401:**

```
WWW-Authenticate: Bearer
```

**Ejemplo:**

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ana@urbe.edu","password":"clave12345"}'
```

---

### 3.5 `GET /auth/me` — Datos del usuario autenticado 🔒

**Uso:** devuelve la información del usuario dueño del token. Sirve para que el frontend muestre "Hola, Ana" o verifique sesión tras recargar.

**Request:** sin body. Requiere `Authorization: Bearer <token>`.

**Response `200 OK`:**

```json
{
  "id": 1,
  "nombre": "Ana Pérez",
  "email": "ana@urbe.edu",
  "creado_en": "2026-09-22 15:30:12"
}
```

> `creado_en` es la fecha del registro tal como la guarda SQLite (`datetime('now')` en UTC, formato `YYYY-MM-DD HH:MM:SS`).

**Errores:**

| Código | Cuándo | Body |
|---|---|---|
| `401 Unauthorized` | Token ausente | `{"detail": "Token de acceso ausente"}` |
| `401 Unauthorized` | Token corrupto / mal firmado / expirado | `{"detail": "Token inválido: <motivo>"}` |
| `401 Unauthorized` | Token válido, pero el usuario ya no existe en la DB | `{"detail": "Usuario no encontrado"}` |

En los tres casos se incluye `WWW-Authenticate: Bearer`.

**Ejemplo:**

```bash
TOKEN="eyJhbGci..."
curl http://127.0.0.1:8000/auth/me -H "Authorization: Bearer $TOKEN"
```

---

## 4. Modelos de datos (schemas)

### 4.1 `RegistroIn`

```typescript
{
  nombre:   string  // 2–100 chars
  email:    string  // email válido, minúsculas
  password: string  // 8–128 chars
}
```

### 4.2 `LoginIn`

```typescript
{
  email:    string  // email válido
  password: string  // 1–128 chars
}
```

### 4.3 `TokenOut`

```typescript
{
  access_token: string  // JWT firmado HS256
  token_type:   "bearer"
  expires_in:   number  // segundos hasta expiración (default 3600)
}
```

### 4.4 `UsuarioOut`

```typescript
{
  id:        number
  nombre:    string
  email:     string
  creado_en: string  // "YYYY-MM-DD HH:MM:SS"
}
```

---

## 5. Flujo completo de autenticación (ejemplo end-to-end)

```bash
# 1. Registro → devuelve token
curl -X POST http://127.0.0.1:8000/auth/registro \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Ana Pérez","email":"ana@urbe.edu","password":"clave12345"}'

# 2. Login → devuelve token nuevo
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ana@urbe.edu","password":"clave12345"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 3. Ruta protegida
curl http://127.0.0.1:8000/auth/me -H "Authorization: Bearer $TOKEN"
```

---

## 6. Códigos de estado HTTP usados

| Código | Significado | Cuándo aparece |
|---|---|---|
| `200 OK` | Éxito | GETs, login |
| `201 Created` | Recurso creado | Registro de usuario |
| `401 Unauthorized` | No autenticado | Token ausente/inválido/expirado, login fallido |
| `409 Conflict` | Conflicto de unicidad | Registro con email duplicado |
| `422 Unprocessable Entity` | Validación fallida | Body con tipos/formatos inválidos |
| `500 Internal Server Error` | Error no controlado | Bug en el servidor (no debería ocurrir) |

---

## 7. Seguridad implementada

| Aspecto | Cómo se cumple |
|---|---|
| **Contraseñas almacenadas** | PBKDF2-HMAC-SHA256 con 600 000 iteraciones + salt aleatorio de 16 bytes por usuario. Nunca se guardan en texto plano. |
| **Comparación de hashes** | `hmac.compare_digest` (tiempo constante) — previene *timing attacks*. |
| **Anti enumeración de emails** | Login ejecuta un hash ficticio aunque el correo no exista, igualando los tiempos de respuesta. El mensaje 401 es genérico. |
| **Tokens** | JWT firmado HS256, expiración por defecto 60 min, `type: "access"`, `sub` = ID. |
| **Tokens sin datos sensibles** | El payload solo lleva el ID. Permisos y datos se consultan a la DB en cada request protegido. |
| **Rutas protegidas** | `Depends(get_current_user)` valida firma + expiración + existencia del usuario. |
| **Email único case-insensitive** | La columna `email` tiene `COLLATE NOCASE UNIQUE`. |
| **Hash fuera de respuestas** | El modelo `CredencialesUsuario` con el hash solo se usa dentro de `auth_service` y nunca se serializa. |

---

## 8. Estructura de la base de datos (estado actual)

### Tabla `usuarios`

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | INTEGER | PK, AUTOINCREMENT |
| `nombre` | TEXT | NOT NULL |
| `email` | TEXT | NOT NULL, UNIQUE, COLLATE NOCASE |
| `password_hash` | TEXT | NOT NULL |
| `creado_en` | TEXT | NOT NULL, default `datetime('now')` |

### Tabla `tareas`

> Ya creada, pero **sin endpoints todavía** (Bloque 3). Se documenta para futura referencia.

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | INTEGER | PK, AUTOINCREMENT |
| `usuario_id` | INTEGER | NOT NULL, FK → `usuarios.id` ON DELETE CASCADE |
| `titulo` | TEXT | NOT NULL |
| `descripcion` | TEXT | — |
| `estado` | TEXT | NOT NULL, default `'pendiente'`, CHECK ∈ {`pendiente`, `en_progreso`, `completada`} |
| `prioridad` | TEXT | NOT NULL, default `'media'`, CHECK ∈ {`baja`, `media`, `alta`, `critica`} |
| `fecha_vencimiento` | TEXT | — (ISO 8601 sugerido) |
| `etiquetas` | TEXT | — (por definir formato en Bloque 3) |
| `creado_en` | TEXT | NOT NULL, default `datetime('now')` |
| `actualizado_en` | TEXT | NOT NULL, default `datetime('now')` |

Índices: `usuario_id`, `estado`, `fecha_vencimiento`.

---

## 9. Endpoints planificados (no implementados todavía)

Sirven de referencia para el equipo de frontend; **no están disponibles aún**.

| Método | Ruta | Descripción | Bloque |
|---|---|---|---|
| `GET` | `/tareas` | Listar tareas del usuario (con filtros y orden) | 3 |
| `POST` | `/tareas` | Crear tarea | 3 |
| `GET` | `/tareas/{id}` | Ver tarea | 3 |
| `PATCH` | `/tareas/{id}` | Actualizar tarea | 3 |
| `PATCH` | `/tareas/{id}/estado` | Mover tarjeta en Kanban | 3 |
| `DELETE` | `/tareas/{id}` | Eliminar tarea | 3 |
| `GET` | `/dashboard` | Métricas del usuario | 4 |
| `GET` | `/notificaciones` | Tareas próximas a vencer | 5 |

---

## 10. Cómo levantar el backend

```bash
# Instalar dependencias
uv sync

# Ejecutar servidor (modo desarrollo, con recarga automática)
uv run uvicorn app.main:app --reload
```

Requiere Python ≥ 3.11 y `uv` instalado.

Variables de entorno relevantes:

| Variable | Default | Descripción |
|---|---|---|
| `DEBUG` | `true` | Modo debug |
| `DB_PATH` | `<proyecto>/data/app.db` | Ruta del archivo SQLite |
| `JWT_SECRET` | `"cambiar-esta-clave-en-produccion"` | Clave de firma HS256 (**¡cambiar antes de producción!**) |
| `JWT_EXPIRATION_MINUTES` | `60` | Vigencia del token en minutos |
