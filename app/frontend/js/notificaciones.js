/**
 * notificaciones.js — Vista Notificaciones.
 *
 *   - Lista agrupada por urgencia (vencida → hoy → manana → esta_semana)
 *   - Filtro `dias_atras` (7 / 30 / 90) en el header
 *   - Click en una notif → abre el modal de edición de la tarea
 */
import { apiFetch } from "./api.js";
import { toast } from "./toast.js";
import { abrirModal } from "./tareas.js";

const URGENCIA_ORDEN = ["vencida", "hoy", "manana", "esta_semana"];
const URGENCIA_LABEL = {
  vencida:    "Vencidas",
  hoy:        "Vencen hoy",
  manana:     "Vencen mañana",
  esta_semana:"Esta semana",
};

const PRIORIDAD_LABEL = { baja: "Baja", media: "Media", alta: "Alta", critica: "Crítica" };

const state = { dias_atras: 30 };
const contenedor = document.querySelector("[data-notif-list]");

function chip(extraClass, text) {
  const s = document.createElement("span");
  s.className = "chip" + (extraClass ? " " + extraClass : "");
  s.textContent = text;
  return s;
}

function formatFecha(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("es-VE", { day: "2-digit", month: "short", year: "numeric" });
}

function diasTexto(n) {
  if (n < 0) return `Hace ${Math.abs(n)} día${Math.abs(n) === 1 ? "" : "s"}`;
  if (n === 0) return "Hoy";
  if (n === 1) return "Mañana";
  return `En ${n} días`;
}

function renderGrupo(urgencia, items) {
  const group = document.createElement("div");
  group.className = "notif-group";

  const header = document.createElement("h2");
  header.style.cssText =
    "font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;" +
    "color:var(--text-muted);margin:1rem 0 0.5rem;";
  header.textContent = `${URGENCIA_LABEL[urgencia]} · ${items.length}`;
  group.appendChild(header);

  items.forEach(n => group.appendChild(renderItem(n)));
  return group;
}

function renderItem(n) {
  const item = document.createElement("div");
  item.className = "notif-item";
  item.dataset.urgencia = n.urgencia;
  item.style.cursor = "pointer";
  item.title = "Click para abrir la tarea";

  // Columna izquierda: chip de prioridad
  item.appendChild(chip(`chip-prioridad-${n.prioridad}`, PRIORIDAD_LABEL[n.prioridad] || n.prioridad));

  // Cuerpo
  const body = document.createElement("div");
  const title = document.createElement("div");
  title.className = "notif-title";
  title.textContent = n.titulo;
  body.appendChild(title);

  const meta = document.createElement("div");
  meta.className = "notif-meta";
  meta.appendChild(chip(`chip-estado-${n.estado}`, n.estado.replace("_", " ")));
  meta.appendChild(document.createTextNode(formatFecha(n.fecha_vencimiento)));
  body.appendChild(meta);

  // Días restantes (derecha)
  const dias = document.createElement("div");
  dias.className = "notif-dias";
  dias.textContent = diasTexto(n.dias_restantes);

  item.append(body, dias);

  item.addEventListener("click", async () => {
    try {
      const t = await apiFetch(`/tareas/${n.tarea_id}`);
      abrirModal(t);
    } catch (err) {
      toast(err.message, "error");
    }
  });

  return item;
}

export async function refrescarNotificaciones() {
  if (!contenedor) return;
  try {
    const data = await apiFetch(`/notificaciones?dias_atras=${state.dias_atras}`);
    contenedor.innerHTML = "";

    if (data.total === 0) {
      const empty = document.createElement("p");
      empty.className = "empty-state";
      empty.innerHTML =
        '<span class="empty-icon">◇</span>Sin notificaciones. Todo bajo control.';
      contenedor.appendChild(empty);
      return;
    }

    // Agrupar respetando orden de urgencia
    const grupos = {};
    data.notificaciones.forEach(n => {
      (grupos[n.urgencia] ||= []).push(n);
    });

    URGENCIA_ORDEN.forEach(u => {
      if (grupos[u]?.length) contenedor.appendChild(renderGrupo(u, grupos[u]));
    });
  } catch (err) {
    toast(err.message, "error");
  }
}

/* ─── Init ────────────────────────────────────────────────────── */
let inicializado = false;

export function initNotificaciones() {
  if (inicializado) return;
  inicializado = true;

  // Selector de ventana temporal
  const selector = document.querySelector('[data-filter-notif="dias_atras"]');
  selector?.addEventListener("change", (e) => {
    state.dias_atras = Number(e.target.value);
    refrescarNotificaciones();
  });

  // Re-render al entrar a la vista o cuando cambian tareas
  document.addEventListener("view:changed", (e) => {
    if (e.detail.view === "notificaciones") refrescarNotificaciones();
  });
}
