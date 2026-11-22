/**
 * tareas.js — Vista Tareas.
 *
 *   - Lista con filtros (busqueda, etiqueta, estado, prioridad, orden)
 *   - Modal crear/editar/eliminar (reutilizable desde kanban.js)
 *   - Toggle completada con el check
 *   - Emite document → CustomEvent("tareas:changed") tras cada mutación
 *     (lo consume app.js para refrescar el badge de notificaciones)
 */
import { apiFetch } from "./api.js";
import { toast } from "./toast.js";

const PRIORIDAD_LABEL = { baja: "Baja", media: "Media", alta: "Alta", critica: "Crítica" };
const ESTADO_LABEL    = { pendiente: "Pendiente", en_progreso: "En progreso", completada: "Completada" };

const state = {
  tareas: [],
  filtros: {
    busqueda: "",
    etiqueta: "",
    estado: "",
    prioridad: "",
    orden_por: "fecha_vencimiento",
  },
};

/* ─── Helpers ──────────────────────────────────────────────────── */
function emitirCambio() {
  document.dispatchEvent(new CustomEvent("tareas:changed"));
}

function formatFecha(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("es-VE", { day: "2-digit", month: "short", year: "numeric" });
}

function chip(extraClass, text) {
  const s = document.createElement("span");
  s.className = "chip" + (extraClass ? " " + extraClass : "");
  s.textContent = text;
  return s;
}

function toLocalInput(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const p = n => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
}

function toISOFromLocal(local) {
  if (!local) return null;
  return new Date(local).toISOString();
}

/* ─── Fetch + render ───────────────────────────────────────────── */
function construirQuery() {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(state.filtros)) {
    if (v) p.set(k, v);
  }
  return p.toString();
}

export async function refrescarTareas() {
  try {
    const qs = construirQuery();
    state.tareas = await apiFetch(`/tareas${qs ? "?" + qs : ""}`);
    renderLista();
  } catch (err) {
    toast(err.message, "error");
  }
}

function renderLista() {
  const ul    = document.querySelector('[data-list="tareas"]');
  const empty = document.querySelector('[data-empty="tareas"]');
  if (!ul) return;

  ul.innerHTML = "";
  if (state.tareas.length === 0) {
    if (empty) empty.hidden = false;
    return;
  }
  if (empty) empty.hidden = true;

  state.tareas.forEach(t => ul.appendChild(renderTarea(t)));
}

function renderTarea(t) {
  const li = document.createElement("li");
  li.className = "task-item";
  li.dataset.id = t.id;
  li.dataset.estado = t.estado;

  // Check completada
  const check = document.createElement("button");
  check.type = "button";
  check.className = "check-btn";
  check.textContent = "✓";
  check.setAttribute(
    "aria-label",
    t.estado === "completada" ? "Marcar como pendiente" : "Marcar como completada"
  );
  check.addEventListener("click", () => toggleCompletada(t));

  // Cuerpo
  const body = document.createElement("div");
  body.className = "task-body";

  const title = document.createElement("div");
  title.className = "task-title";
  title.textContent = t.titulo;
  body.appendChild(title);

  if (t.descripcion) {
    const desc = document.createElement("div");
    desc.className = "task-desc";
    desc.textContent = t.descripcion;
    body.appendChild(desc);
  }

  const meta = document.createElement("div");
  meta.className = "task-meta";
  meta.appendChild(chip(`chip-estado-${t.estado}`, ESTADO_LABEL[t.estado] || t.estado));
  meta.appendChild(chip(`chip-prioridad-${t.prioridad}`, PRIORIDAD_LABEL[t.prioridad] || t.prioridad));

  if (t.fecha_vencimiento) {
    const vencida = t.estado !== "completada" && new Date(t.fecha_vencimiento) < new Date();
    meta.appendChild(
      chip(vencida ? "chip-vencida" : "", (vencida ? "⚠ " : "") + formatFecha(t.fecha_vencimiento))
    );
  }

  (t.etiquetas || []).forEach(tag => meta.appendChild(chip("", `#${tag}`)));
  body.appendChild(meta);

  // Acciones (editar/eliminar)
  const actions = document.createElement("div");
  actions.className = "task-actions";

  const editBtn = document.createElement("button");
  editBtn.type = "button";
  editBtn.className = "icon-btn";
  editBtn.textContent = "✎";
  editBtn.setAttribute("aria-label", "Editar");
  editBtn.addEventListener("click", () => abrirModal(t));

  const delBtn = document.createElement("button");
  delBtn.type = "button";
  delBtn.className = "icon-btn";
  delBtn.textContent = "🗑";
  delBtn.setAttribute("aria-label", "Eliminar");
  delBtn.addEventListener("click", () => eliminar(t));

  actions.append(editBtn, delBtn);

  li.append(check, body, actions);
  return li;
}

/* ─── Acciones sobre tareas ────────────────────────────────────── */
async function toggleCompletada(t) {
  const nuevo = t.estado === "completada" ? "pendiente" : "completada";
  try {
    await apiFetch(`/tareas/${t.id}/estado`, {
      method: "PATCH",
      body: JSON.stringify({ estado: nuevo }),
    });
    emitirCambio();
    await refrescarTareas();
  } catch (err) {
    toast(err.message, "error");
  }
}

async function eliminar(t) {
  if (!confirm(`¿Eliminar la tarea "${t.titulo}"?`)) return;
  try {
    await apiFetch(`/tareas/${t.id}`, { method: "DELETE" });
    toast("Tarea eliminada", "success");
    emitirCambio();
    await refrescarTareas();
  } catch (err) {
    toast(err.message, "error");
  }
}

/* ─── Modal crear / editar ─────────────────────────────────────── */
const modal     = document.querySelector('[data-modal="tarea"]');
const formTarea = document.querySelector('[data-form="tarea"]');

function showErrorModal(msg) {
  const el = document.querySelector('[data-error-for="tarea"]');
  if (!el) return;
  el.textContent = msg;
  el.hidden = !msg;
}

export function abrirModal(t = null) {
  if (!modal || !formTarea) return;
  formTarea.reset();
  showErrorModal("");

  document.querySelector("[data-modal-title]").textContent =
    t ? "Editar tarea" : "Nueva tarea";

  if (t) {
    formTarea.elements.id.value            = t.id;
    formTarea.elements.titulo.value        = t.titulo;
    formTarea.elements.descripcion.value   = t.descripcion || "";
    formTarea.elements.estado.value        = t.estado;
    formTarea.elements.prioridad.value     = t.prioridad;
    formTarea.elements.fecha_vencimiento.value = toLocalInput(t.fecha_vencimiento);
    formTarea.elements.etiquetas.value     = (t.etiquetas || []).join(", ");
  }
  modal.showModal();
}

async function submitModal(e) {
  e.preventDefault();

  const fd     = new FormData(formTarea);
  const id     = fd.get("id");
  const titulo = (fd.get("titulo") || "").trim();
  if (!titulo) { showErrorModal("El título es obligatorio"); return; }

  const etiquetasRaw = (fd.get("etiquetas") || "").trim();
  const etiquetas = etiquetasRaw
    ? etiquetasRaw.split(",").map(s => s.trim()).filter(Boolean)
    : [];

  const payload = {
    titulo,
    descripcion:       (fd.get("descripcion") || "").trim() || null,
    estado:            fd.get("estado"),
    prioridad:         fd.get("prioridad"),
    fecha_vencimiento: toISOFromLocal(fd.get("fecha_vencimiento")),
    etiquetas,
  };

  const btn  = formTarea.querySelector('button[type="submit"]');
  const prev = btn.textContent;
  btn.disabled = true;
  btn.textContent = "Guardando…";
  showErrorModal("");

  try {
    if (id) {
      await apiFetch(`/tareas/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
      toast("Tarea actualizada", "success");
    } else {
      await apiFetch("/tareas",       { method: "POST",  body: JSON.stringify(payload) });
      toast("Tarea creada", "success");
    }
    modal.close();
    emitirCambio();
    await refrescarTareas();
  } catch (err) {
    showErrorModal(err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = prev;
  }
}

/* ─── Filtros (toolbar) ────────────────────────────────────────── */
function setupFiltros() {
  const busq  = document.querySelector('[data-filter="busqueda"]');
  const etiq  = document.querySelector('[data-filter="etiqueta"]');
  const est   = document.querySelector('[data-filter="estado"]');
  const prio  = document.querySelector('[data-filter="prioridad"]');
  const orden = document.querySelector('[data-filter="orden_por"]');

  let timer = null;
  const aplicar = (key, val, delay = 0) => {
    state.filtros[key] = val;
    clearTimeout(timer);
    timer = setTimeout(refrescarTareas, delay);
  };

  busq?.addEventListener("input",  e => aplicar("busqueda",  e.target.value.trim(), 300));
  etiq?.addEventListener("input",  e => aplicar("etiqueta",  e.target.value.trim(), 300));
  est?.addEventListener("change",  e => aplicar("estado",    e.target.value));
  prio?.addEventListener("change", e => aplicar("prioridad", e.target.value));
  orden?.addEventListener("change",e => aplicar("orden_por", e.target.value));
}

/* ─── Init ─────────────────────────────────────────────────────── */
let inicializado = false;

export function initTareas() {
  if (inicializado) return;
  inicializado = true;

  setupFiltros();

  formTarea?.addEventListener("submit", submitModal);
  document.querySelectorAll("[data-close-modal]").forEach(btn => {
    btn.addEventListener("click", () => modal?.close());
  });
  modal?.addEventListener("click", (e) => {
    if (e.target === modal) modal.close();
  });

  // Refresco cuando el usuario vuelve a la vista Tareas
  document.addEventListener("view:changed", (e) => {
    if (e.detail.view === "tareas") refrescarTareas();
  });

  refrescarTareas();
}
