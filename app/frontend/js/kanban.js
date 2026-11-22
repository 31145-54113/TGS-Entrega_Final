/**
 * kanban.js — Vista Kanban con drag & drop nativo HTML5.
 *
 *   - 3 columnas: pendiente | en_progreso | completada
 *   - Arrastrar tarjeta a otra columna → PATCH /tareas/{id}/estado
 *   - Click en tarjeta → abre el modal de edición (reusa tareas.js)
 *   - Se re-renderiza al recibir "view:changed" a kanban o "tareas:changed"
 */
import { apiFetch } from "./api.js";
import { toast } from "./toast.js";
import { abrirModal } from "./tareas.js";

const COLUMNAS = [
  { estado: "pendiente",   titulo: "Pendiente" },
  { estado: "en_progreso", titulo: "En progreso" },
  { estado: "completada",  titulo: "Completada" },
];

const PRIORIDAD_LABEL = { baja: "Baja", media: "Media", alta: "Alta", critica: "Crítica" };

const board = document.querySelector("[data-kanban]");

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
  return d.toLocaleDateString("es-VE", { day: "2-digit", month: "short" });
}

/* ─── Render ──────────────────────────────────────────────────── */
function renderColumna(col, tareas) {
  const wrap = document.createElement("section");
  wrap.className = "kanban-col";
  wrap.dataset.col = col.estado;

  // Header
  const header = document.createElement("header");
  header.className = "kanban-col-header";

  const title = document.createElement("span");
  title.className = "kanban-col-title";
  title.textContent = col.titulo;

  const count = document.createElement("span");
  count.className = "kanban-count";
  count.textContent = String(tareas.length);

  header.append(title, count);

  // Contenedor de tarjetas
  const cards = document.createElement("div");
  cards.className = "kanban-cards";
  cards.dataset.dropzone = col.estado;

  if (tareas.length === 0) {
    const empty = document.createElement("p");
    empty.style.cssText =
      "font-size:0.75rem;color:var(--text-dim);text-align:center;padding:1rem 0;margin:0;";
    empty.textContent = "Sin tareas";
    cards.appendChild(empty);
  } else {
    tareas.forEach(t => cards.appendChild(renderCard(t)));
  }

  // Dropzone: al arrastrar sobre la columna, se resalta
  cards.addEventListener("dragover", (e) => {
    e.preventDefault();
    wrap.classList.add("is-drop-target");
  });
  cards.addEventListener("dragleave", (e) => {
    if (!cards.contains(e.relatedTarget)) wrap.classList.remove("is-drop-target");
  });
  cards.addEventListener("drop", (e) => {
    e.preventDefault();
    wrap.classList.remove("is-drop-target");
    const id = Number(e.dataTransfer.getData("text/plain"));
    const desde = e.dataTransfer.getData("from");
    if (id && desde !== col.estado) moverTarea(id, col.estado);
  });

  wrap.append(header, cards);
  return wrap;
}

function renderCard(t) {
  const card = document.createElement("article");
  card.className = "kanban-card";
  card.draggable = true;
  card.dataset.id = t.id;
  card.dataset.estado = t.estado;

  const title = document.createElement("div");
  title.className = "kanban-card-title";
  title.textContent = t.titulo;
  card.appendChild(title);

  const meta = document.createElement("div");
  meta.className = "kanban-card-meta";
  meta.appendChild(chip(`chip-prioridad-${t.prioridad}`, PRIORIDAD_LABEL[t.prioridad] || t.prioridad));

  if (t.fecha_vencimiento) {
    const vencida = t.estado !== "completada" && new Date(t.fecha_vencimiento) < new Date();
    meta.appendChild(
      chip(vencida ? "chip-vencida" : "", (vencida ? "⚠ " : "") + formatFecha(t.fecha_vencimiento))
    );
  }
  (t.etiquetas || []).forEach(tag => meta.appendChild(chip("", `#${tag}`)));
  card.appendChild(meta);

  // Click (no drag) → modal de edición
  card.addEventListener("click", () => abrirModal(t));

  // Drag start
  card.addEventListener("dragstart", (e) => {
    card.classList.add("is-dragging");
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", String(t.id));
    e.dataTransfer.setData("from", t.estado);
  });
  card.addEventListener("dragend", () => card.classList.remove("is-dragging"));

  return card;
}

/* ─── Fetch + render global ───────────────────────────────────── */
export async function refrescarKanban() {
  if (!board) return;
  try {
    const tareas = await apiFetch("/tareas");
    board.innerHTML = "";
    COLUMNAS.forEach(col => {
      const enCol = tareas.filter(t => t.estado === col.estado);
      board.appendChild(renderColumna(col, enCol));
    });
  } catch (err) {
    toast(err.message, "error");
  }
}

/* ─── Mover tarea (PATCH /estado) ─────────────────────────────── */
async function moverTarea(id, nuevoEstado) {
  try {
    await apiFetch(`/tareas/${id}/estado`, {
      method: "PATCH",
      body: JSON.stringify({ estado: nuevoEstado }),
    });
    document.dispatchEvent(new CustomEvent("tareas:changed"));
    await refrescarKanban();
  } catch (err) {
    toast(err.message, "error");
  }
}

/* ─── Init ────────────────────────────────────────────────────── */
let inicializado = false;

export function initKanban() {
  if (inicializado || !board) return;
  inicializado = true;

  // Refresca cuando se navega a kanban o cuando cambian las tareas
  document.addEventListener("view:changed", (e) => {
    if (e.detail.view === "kanban") refrescarKanban();
  });
  document.addEventListener("tareas:changed", () => {
    if (!document.querySelector('[data-view="kanban"]').hidden) refrescarKanban();
  });

  // Carga inicial silenciosa (aunque no esté visible)
  refrescarKanban();
}
