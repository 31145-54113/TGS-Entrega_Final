# API Backend — Bloques 3 y 4 (Tareas + Dashboard)

**Versión del documento:** 0.2
**Versión del backend:** 0.1.0
**Complementa a:** `API_Backend_v0.1.md` (autenticación)
**Cátedra:** Teoría General de Sistemas · Sección N-711 · URBE

> Este documento describe **únicamente** los endpoints de Tareas (Bloque 3)
> y del Dashboard analítico (Bloque 4). La autenticación (registro, login,
> `/auth/me`) está documentada en `API_Backend_v0.1.md` y no se repite aquí.

---

## 1. Cambios estructurales respecto al Bloque 2

### 1.1 Nueva columna `tareas.completado_en`

A partir del Bloque 4 la tabla `tareas` incluye la columna:

| Columna | Tipo | Descripción |
|---|---|---|
| `completado_en` | TEXT (nullable) | Fecha/hora UTC (`YYYY-MM-DD HH:MM:SS`) en la que la tarea pasó a estado `completada`. Se **limpia** automáticamente si la tarea vuelve a un estado no completado. |

**Reglas de negocio asociadas:**

- Se llena **automáticamente** cuando una tarea pasa a `completada` desde cualquier otro estado.
- Se borra (queda `NULL`) si una tarea `completada` vuelve a `pendiente` o `en_progreso`.
- Si una tarea **se crea directamente** en estado `completada`, `completado_en` se setea al momento de creación.
- **El cliente nunca lo envía ni lo modifica**: no aparece en `TareaCreate` ni en `TareaUpdate`.

> Sirve de base para los cálculos de puntualidad y series semanales del Dashboard.

### 1.2 Migración aplicada

Sobre una base de datos preexistente del Bloque 3:

```sql
ALTER TABLE tareas ADD COLUMN completado_en TEXT;
UPDATE tareas SET completado_en = actualizado_en
 WHERE estado = 'completada' AND completado_en IS NULL;
```

Las tareas completadas antes de la migración toman su `actualizado_en` como aproximación.

---

## 2. Convenciones heredadas del Bloque 2

- **Base URL:** `http://127.0.0.1:8000`
- **Auth:** `Authorization: Bearer <token>` en todas las rutas marcadas 🔒.
- **Errores de negocio:** `{"detail": "<mensaje>"}`
- **Errores de validación:** 422 con lista de errores por campo.
- **Fechas en JSON:** ISO 8601 con zona UTC (`2026-11-28T23:59:00Z`).
- **Fechas en la DB:** `YYYY-MM-DD HH:MM:SS` en UTC.
- **`null` explícito en PATCH:** para limpiar un campo nullable, se envía `null` explícitamente (ver §3.5).

---

## 3. Endpoints de Tareas

Todas las rutas requieren autenticación 🔒. El backend **siempre** filtra por `usuario_id` obtenido del token — un usuario nunca puede ver, editar ni borrar tareas de otro.

**Respuesta ante acceso a tarea ajena o inexistente:** `404`, nunca `403`. Esto evita filtrar si una tarea existe (protección contra enumeración).

### 3.1 Tabla resumen

| Método | Ruta | Descripción | Códigos |
|---|---|---|---|
| `GET` | `/tareas` | Listar tareas del usuario (con filtros y orden) | 200, 401, 422 |
| `POST` | `/tareas` | Crear tarea | 201, 401, 422 |
| `GET` | `/tareas/{id}` | Ver una tarea | 200, 401, 404 |
| `PATCH` | `/tareas/{id}` | Actualización parcial | 200, 401, 404, 422 |
| `PATCH` | `/tareas/{id}/estado` | Cambiar estado (para Kanban) | 200, 401, 404, 422 |
| `DELETE` | `/tareas/{id}` | Eliminar tarea | 204, 401, 404 |

---

### 3.2 `GET /tareas` — Listar tareas 🔒

**Uso:** alimenta tanto la vista de lista como el tablero Kanban (agrupando por `estado`) y la vista de "próximas a vencer".

**Query params (todos opcionales, combinables):**

| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `estado` | enum | — | `pendiente` \| `en_progreso` \| `completada` |
| `prioridad` | enum | — | `baja` \| `media` \| `alta` \| `critica` |
| `etiqueta` | string | — | Filtra tareas que contengan exactamente esa etiqueta (case-insensitive, comparación por token, no substring) |
| `busqueda` | string | — | Búsqueda `LIKE %texto%` sobre `titulo` y `descripcion` |
| `vencidas` | bool | `false` | Solo tareas con `fecha_vencimiento < now()` y estado ≠ `completada` |
| `proximas_dias` | int (1–365) | — | Solo tareas que vencen en los próximos N días y estado ≠ `completada` |
| `orden_por` | enum | `fecha_vencimiento` | `prioridad` \| `fecha_vencimiento` \| `creado_en` \| `actualizado_en` \| `titulo` |
| `orden` | enum | `asc` | `asc` \| `desc` |

**Reglas de ordenamiento:**

- `orden_por=prioridad` → `critica > alta > media > baja` (orden lógico, no alfabético).
- `orden_por=fecha_vencimiento` → las tareas sin fecha van **al final**, independientemente de `orden`.
- `orden_por=titulo` → comparación case-insensitive (`COLLATE NOCASE`).
- Desempate secundario: `id ASC` para resultados estables.

**Response `200 OK`:** `list[TareaOut]` (ver §4.1). Lista vacía `[]` si no hay tareas.

**Ejemplo:**

```bash
# Tareas de prioridad alta ordenadas por vencimiento
curl "http://127.0.0.1:8000/tareas?prioridad=alta&orden_por=fecha_vencimiento&orden=asc" \
  -H "Authorization: Bearer $TOKEN"

# Tareas vencidas pendientes
curl "http://127.0.0.1:8000/tareas?vencidas=true" -H "Authorization: Bearer $TOKEN"

# Tareas que vencen esta semana
curl "http://127.0.0.1:8000/tareas?proximas_dias=7" -H "Authorization: Bearer $TOKEN"

# Búsqueda por texto + filtro por etiqueta
curl "http://127.0.0.1:8000/tareas?busqueda=informe&etiqueta=tgs" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 3.3 `POST /tareas` — Crear tarea 🔒

**Request body (`TareaCreate`):**

| Campo | Tipo | Obligatorio | Restricciones |
|---|---|---|---|
| `titulo` | string | Sí | 1–200 caracteres. Se aplica `.strip()`. |
| `descripcion` | string \| null | No | Máximo 5000 caracteres. |
| `estado` | enum | No | Default `pendiente`. |
| `prioridad` | enum | No | Default `media`. |
| `fecha_vencimiento` | ISO datetime \| null | No | Ej: `"2026-11-28T23:59:00Z"`. Se convierte a UTC. |
| `etiquetas` | list[str] | No | Default `[]`. Ver §5.1 para reglas. |

**Response `201 Created`:** `TareaOut` con `completado_en` ya resuelto (ver §4.1).

**Errores:**

| Código | Cuándo |
|---|---|
| `422` | Título vacío, campos extra (`extra="forbid"`), etiquetas inválidas (>10, >30 chars, con `,` `%` `_` `\`), fecha mal formada. |
| `401` | Token ausente o inválido. |

**Ejemplo:**

```bash
curl -X POST http://127.0.0.1:8000/tareas \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Entregar informe TGS",
    "descripcion": "Fase 3 del proyecto",
    "prioridad": "alta",
    "fecha_vencimiento": "2026-11-28T23:59:00Z",
    "etiquetas": ["tgs", "urbe"]
  }'
```

---

### 3.4 `GET /tareas/{id}` — Ver tarea 🔒

**Response `200 OK`:** `TareaOut`.

**Errores:** `404` si no existe o pertenece a otro usuario.

```bash
curl http://127.0.0.1:8000/tareas/1 -H "Authorization: Bearer $TOKEN"
```

---

### 3.5 `PATCH /tareas/{id}` — Actualización parcial 🔒

**Request body (`TareaUpdate`):** todos los campos son opcionales, pero **debe enviarse al menos uno** (si no → `422`).

| Campo | Tipo | Notas |
|---|---|---|
| `titulo` | string \| null | Si se envía, no puede ser `null` ni vacío. |
| `descripcion` | string \| null | Enviar `null` **limpia** el campo. |
| `estado` | enum \| null | Mismo efecto que `PATCH /estado`. |
| `prioridad` | enum \| null | — |
| `fecha_vencimiento` | ISO datetime \| null | Enviar `null` **limpia** la fecha. |
| `etiquetas` | list[str] \| null | Enviar `[]` o `null` limpia las etiquetas. |

**Semántica clave — ausente vs `null`:**

- **Campo ausente** en el body → **no se toca**.
- **Campo = `null`** → se **limpia** (solo en campos nullables: `descripcion`, `fecha_vencimiento`, `etiquetas`).
- **Campo con valor** → se **reemplaza**.

Esto se implementa con `model_dump(exclude_unset=True)`, por eso distinguir "no enviado" de "enviado como null" funciona correctamente.

**Response `200 OK`:** `TareaOut` actualizado. El campo `actualizado_en` se refresca automáticamente.

**Errores:** `404` si no existe / no es del usuario; `422` si no se envía ningún campo o los valores no cumplen restricciones.

**Ejemplo — cambiar solo la descripción:**

```bash
curl -X PATCH http://127.0.0.1:8000/tareas/1 \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"descripcion": "Actualizada"}'
```

**Ejemplo — limpiar descripción y fecha límite (dejarlas en null):**

```bash
curl -X PATCH http://127.0.0.1:8000/tareas/1 \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"descripcion": null, "fecha_vencimiento": null}'
```

---

### 3.6 `PATCH /tareas/{id}/estado` — Cambiar estado 🔒

**Uso:** endpoint dedicado para el **drag & drop** del Kanban. Evita que el frontend tenga que construir un `PATCH` genérico solo para mover tarjetas.

**Request body (`EstadoUpdate`):**

```json
{ "estado": "en_progreso" }
```

**Efectos secundarios automáticos:**

- Si el nuevo estado es `completada` y el anterior no lo era → se setea `completado_en` a la hora actual.
- Si el nuevo estado NO es `completada` y el anterior sí lo era → `completado_en = null`.

**Response `200 OK`:** `TareaOut` con `completado_en` actualizado.

**Errores:** `404` (no existe / no es del usuario), `422` (estado inválido).

```bash
curl -X PATCH http://127.0.0.1:8000/tareas/1/estado \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"estado": "completada"}'
```

---

### 3.7 `DELETE /tareas/{id}` — Eliminar tarea 🔒

**Response `204 No Content`:** sin body.

**Errores:** `404` si no existe / no es del usuario.

```bash
curl -X DELETE http://127.0.0.1:8000/tareas/1 -H "Authorization: Bearer $TOKEN" -i
# HTTP/1.1 204 No Content
```

---

## 4. Modelos de datos

### 4.1 `TareaOut`

```typescript
{
  id:                number
  titulo:            string
  descripcion:       string | null
  estado:            "pendiente" | "en_progreso" | "completada"
  prioridad:         "baja" | "media" | "alta" | "critica"
  fecha_vencimiento: string | null   // ISO 8601 UTC
  etiquetas:         string[]
  completado_en:     string | null   // ISO 8601 UTC, auto-gestionado
  creado_en:         string          // "YYYY-MM-DD HH:MM:SS" (UTC, formato DB)
  actualizado_en:    string          // "YYYY-MM-DD HH:MM:SS" (UTC, formato DB)
}
```

> `usuario_id` **no** se expone: el cliente ya sabe que la tarea es suya.
>
> Nota sobre formatos: `fecha_vencimiento` y `completado_en` viajan como ISO 8601 (por ser campos `datetime` de Pydantic). `creado_en` y `actualizado_en` viajan tal cual los genera SQLite, para no perder información histórica.

### 4.2 `TareaCreate`

```typescript
{
  titulo:            string        // 1–200 chars
  descripcion?:      string | null // máx 5000
  estado?:           "pendiente" | "en_progreso" | "completada"  // default: "pendiente"
  prioridad?:        "baja" | "media" | "alta" | "critica"       // default: "media"
  fecha_vencimiento?: string | null
  etiquetas?:        string[]      // default: []
}
```

### 4.3 `TareaUpdate`

Todos los campos son opcionales. **Al menos uno debe enviarse.**

```typescript
{
  titulo?:            string | null
  descripcion?:       string | null
  estado?:            "pendiente" | "en_progreso" | "completada" | null
  prioridad?:         "baja" | "media" | "alta" | "critica" | null
  fecha_vencimiento?: string | null
  etiquetas?:         string[] | null
}
```

### 4.4 `EstadoUpdate`

```typescript
{ estado: "pendiente" | "en_progreso" | "completada" }
```

---

## 5. Reglas de etiquetas

| Regla | Detalle |
|---|---|
| **Normalización** | Se convierten a minúsculas (`TGS` → `tgs`). |
| **Trim** | Se eliminan espacios al inicio/final (`  tgs  ` → `tgs`). |
| **Vacías** | Se descartan silenciosamente (`["", "  "]` → `[]`). |
| **Deduplicación** | Si llegan duplicadas, se conserva la primera ocurrencia. |
| **Largo máximo por etiqueta** | 30 caracteres. |
| **Caracteres prohibidos** | `,` `%` `_` `\` — se rechaza con `422` si aparecen. Se prohíben por el formato interno (separadas por coma) y por el `LIKE` del filtro. |
| **Cantidad máxima** | 10 etiquetas por tarea. |

**Almacenamiento en DB:** TEXT con etiquetas unidas por `,` (ej: `"tgs,urbe,informe"`). El filtro `?etiqueta=tgs` hace match exacto por token, no substring.

---

## 6. Endpoint de Dashboard

### 6.1 `GET /dashboard` 🔒

**Uso:** alimenta el panel analítico del frontend. Devuelve todas las métricas en una sola llamada para evitar round-trips.

**Request:** sin body. Requiere `Bearer token`.

**Response `200 OK` (`DashboardOut`):**

```json
{
  "resumen": {
    "total_tareas": 5,
    "por_estado": { "pendiente": 2, "en_progreso": 1, "completada": 2 },
    "por_prioridad": { "baja": 0, "media": 2, "alta": 2, "critica": 1 },
    "vencidas_pendientes": 1,
    "proximas_7_dias": 3
  },
  "puntualidad": {
    "completadas_con_fecha": 2,
    "a_tiempo": 1,
    "tarde": 1,
    "tasa": 50.0
  },
  "semanal": {
    "ultimos_7_dias": 2,
    "semana_anterior": 0,
    "variacion_pct": null,
    "promedio_diario": 0.29
  },
  "serie_diaria": [
    { "fecha": "2026-11-16", "completadas": 0 },
    { "fecha": "2026-11-17", "completadas": 0 },
    { "fecha": "2026-11-18", "completadas": 1 },
    { "fecha": "2026-11-19", "completadas": 0 },
    { "fecha": "2026-11-20", "completadas": 0 },
    { "fecha": "2026-11-21", "completadas": 1 },
    { "fecha": "2026-11-22", "completadas": 0 }
  ],
  "tiempo_completado": {
    "promedio_horas": 36.5,
    "mediana_horas": 24.0
  }
}
```

### 6.2 Descripción de cada bloque

#### `resumen`

| Campo | Significado |
|---|---|
| `total_tareas` | Cantidad total de tareas del usuario (todos los estados). |
| `por_estado` | Conteo por estado. Siempre incluye las tres claves (con `0` si no hay). |
| `por_prioridad` | Conteo por prioridad. Siempre incluye las cuatro claves. |
| `vencidas_pendientes` | Tareas con `fecha_vencimiento < now()` y estado ≠ `completada`. |
| `proximas_7_dias` | Tareas que vencen entre `now()` y `now()+7d`, no completadas. |

#### `puntualidad`

Se calcula **solo sobre tareas completadas que tienen `fecha_vencimiento` y `completado_en`**.

| Campo | Significado |
|---|---|
| `completadas_con_fecha` | Denominador: tareas con ambas fechas. |
| `a_tiempo` | `completado_en <= fecha_vencimiento`. |
| `tarde` | `completado_en > fecha_vencimiento`. |
| `tasa` | Porcentaje `a_tiempo / completadas_con_fecha × 100`, redondeado a 2 decimales. **`null`** si `completadas_con_fecha = 0` (evita división por cero). |

#### `semanal`

| Campo | Significado |
|---|---|
| `ultimos_7_dias` | Tareas completadas en `[now()-7d, now()]`. |
| `semana_anterior` | Tareas completadas en `[now()-14d, now()-7d)` — **rango cerrado-abierto**, no se solapa con el anterior. |
| `variacion_pct` | `(ultimos_7 - anterior) / anterior × 100`, redondeado. **`null`** si `semana_anterior = 0`. |
| `promedio_diario` | `ultimos_7_dias / 7`, redondeado a 2 decimales. |

#### `serie_diaria`

Siempre devuelve **exactamente 7 elementos**, uno por día, del más antiguo al más reciente. Los días sin actividad aparecen con `completadas: 0`. **Listo para graficar** sin post-procesamiento.

- `fecha`: `YYYY-MM-DD`.
- Zona horaria: UTC (consistente con el resto del sistema).

#### `tiempo_completado`

Se calcula sobre todas las tareas completadas con `completado_en` no nulo, como `(completado_en - creado_en)` en horas.

| Campo | Significado |
|---|---|
| `promedio_horas` | Media aritmética. `null` si no hay datos. |
| `mediana_horas` | Mediana. Más robusta que el promedio ante outliers. `null` si no hay datos. |

### 6.3 Casos borde y valores `null`

La API **nunca falla** por falta de datos: devuelve `null` o `0` cuando no puede calcular algo.

| Situación | Resultado |
|---|---|
| Usuario sin tareas | `total_tareas: 0`, distribuciones en `0`, `tasa: null`, `variacion_pct: null`, `promedio_horas: null`, `mediana_horas: null`, serie con 7 ceros. |
| Sin tareas completadas con fecha límite | `puntualidad.tasa: null` |
| Semana anterior sin completadas | `semanal.variacion_pct: null` |
| Sin tareas completadas | `tiempo_completado.*: null` |

**Ejemplo:**

```bash
curl http://127.0.0.1:8000/dashboard -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

---

## 7. Modelos de respuesta del Dashboard

### 7.1 `DashboardOut`

```typescript
{
  resumen:           ResumenOut
  puntualidad:       PuntualidadOut
  semanal:           SemanalOut
  serie_diaria:      DiaCompletadas[]
  tiempo_completado: TiempoCompletadoOut
}
```

### 7.2 `ResumenOut`

```typescript
{
  total_tareas:          number
  por_estado:            ConteoPorEstado
  por_prioridad:         ConteoPorPrioridad
  vencidas_pendientes:   number
  proximas_7_dias:       number
}
```

### 7.3 `ConteoPorEstado`

```typescript
{ pendiente: number; en_progreso: number; completada: number }
```

### 7.4 `ConteoPorPrioridad`

```typescript
{ baja: number; media: number; alta: number; critica: number }
```

### 7.5 `PuntualidadOut`

```typescript
{
  completadas_con_fecha: number
  a_tiempo:              number
  tarde:                 number
  tasa:                  number | null   // 0–100
}
```

### 7.6 `SemanalOut`

```typescript
{
  ultimos_7_dias:  number
  semana_anterior: number
  variacion_pct:   number | null   // puede ser negativo
  promedio_diario: number
}
```

### 7.7 `DiaCompletadas`

```typescript
{ fecha: string /* YYYY-MM-DD */; completadas: number }
```

### 7.8 `TiempoCompletadoOut`

```typescript
{
  promedio_horas: number | null
  mediana_horas:  number | null
}
```

---

## 8. Códigos de estado usados en estos bloques

| Código | Significado | Cuándo aparece |
|---|---|---|
| `200 OK` | Éxito | GET, PATCH, GET /dashboard |
| `201 Created` | Recurso creado | POST /tareas |
| `204 No Content` | Eliminado, sin body | DELETE /tareas/{id} |
| `401 Unauthorized` | Token ausente / inválido | Cualquier ruta 🔒 sin token válido |
| `404 Not Found` | Tarea inexistente **o** de otro usuario | GET/PATCH/DELETE por id |
| `422 Unprocessable Entity` | Validación | Body/fechas/etiquetas inválidas |

---

## 9. Flujo de ejemplo end-to-end

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ana@urbe.edu","password":"clave12345"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2. Crear tres tareas con distintos estados y prioridades
curl -s -X POST http://127.0.0.1:8000/tareas -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"titulo":"Informe TGS","prioridad":"alta","fecha_vencimiento":"2026-11-28T23:59:00Z","etiquetas":["tgs"]}'

curl -s -X POST http://127.0.0.1:8000/tareas -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"titulo":"Mapa conceptual","prioridad":"media","etiquetas":["tgs","mapa"]}'

curl -s -X POST http://127.0.0.1:8000/tareas -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"titulo":"Exposición","prioridad":"critica","fecha_vencimiento":"2026-11-25T14:00:00Z"}'

# 3. Mover la 1 a en_progreso (Kanban)
curl -s -X PATCH http://127.0.0.1:8000/tareas/1/estado -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"estado":"en_progreso"}'

# 4. Completar la 2 → completado_en se setea automáticamente
curl -s -X PATCH http://127.0.0.1:8000/tareas/2/estado -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"estado":"completada"}'

# 5. Ver el dashboard con datos reales
curl -s http://127.0.0.1:8000/dashboard -H "Authorization: Bearer $TOKEN" | python -m json.tool

# 6. Ver las próximas a vencer (lo que en el Bloque 5 será /notificaciones)
curl -s "http://127.0.0.1:8000/tareas?proximas_dias=7" -H "Authorization: Bearer $TOKEN"
```

---

## 10. Notas de implementación (para el equipo)

- **`completado_en`** se gestiona exclusivamente en `services/tarea_service.py` (`_marcar_completado`). El repositorio solo recibe el valor ya calculado.
- El **filtro por etiqueta** usa `',' || COALESCE(etiquetas,'') || ',' LIKE '%,tag,%'` para garantizar match exacto por token (evita que `tgs` matchee con `tgsv`).
- El **dashboard** consulta varias veces la tabla `tareas`, pero todos los queries usan los índices `idx_tareas_usuario`, `idx_tareas_estado`, `idx_tareas_vencimiento`. Con el volumen esperado (<10k filas por usuario) es instantáneo.
- El endpoint `/dashboard` está aislado en su propio módulo (`dashboard_repo.py` + `dashboard_service.py`) para no mezclar queries analíticas con el CRUD transaccional.
- Los **nullables en PATCH** funcionan por `model_dump(exclude_unset=True)`: campos ausentes NO viajan al repo, campos con `null` sí (para limpiarlos).

---

## 11. Planificado para próximos bloques

| Método | Ruta | Descripción | Bloque |
|---|---|---|---|
| `GET` | `/notificaciones` | Tareas próximas a vencer agrupadas por urgencia | 5 |
| `GET` | `/notificaciones/conteo` | Solo el badge numérico (para el header del frontend) | 5 |
