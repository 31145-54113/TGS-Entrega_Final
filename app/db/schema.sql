PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS usuarios (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre        TEXT    NOT NULL,
    email         TEXT    NOT NULL COLLATE NOCASE UNIQUE,
    password_hash TEXT    NOT NULL,
    creado_en     TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tareas (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id        INTEGER NOT NULL,
    titulo            TEXT    NOT NULL,
    descripcion       TEXT,
    estado            TEXT    NOT NULL DEFAULT 'pendiente'
                      CHECK (estado IN ('pendiente', 'en_progreso', 'completada')),
    prioridad         TEXT    NOT NULL DEFAULT 'media'
                      CHECK (prioridad IN ('baja', 'media', 'alta', 'critica')),
    fecha_vencimiento TEXT,
    etiquetas         TEXT,
    completado_en     TEXT,
    creado_en         TEXT    NOT NULL DEFAULT (datetime('now')),
    actualizado_en    TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_tareas_usuario       ON tareas(usuario_id);
CREATE INDEX IF NOT EXISTS idx_tareas_estado        ON tareas(estado);
CREATE INDEX IF NOT EXISTS idx_tareas_vencimiento   ON tareas(fecha_vencimiento);
