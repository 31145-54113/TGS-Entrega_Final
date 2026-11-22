/**
 * dashboard.js — Vista Dashboard con Chart.js.
 *
 *   - 4 stat-cards: total_tareas, tasa, proximas_7_dias, vencidas_pendientes
 *   - 3 gráficos: doughnut por estado, bar por prioridad, line serie 7 días
 *   - Re-render en "view:changed" a dashboard o "tareas:changed"
 *   - Respeta el tema para colores del gráfico
 */
import { apiFetch } from "./api.js";
import { toast } from "./toast.js";

const charts = {}; // instancias por canvas

/* ─── Colores desde CSS variables ─────────────────────────────── */
function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function paleta() {
  return {
    accent:  cssVar("--accent"),
    text:    cssVar("--text-muted"),
    border:  cssVar("--border"),
    success: cssVar("--success"),
    warning: cssVar("--warning"),
    danger:  cssVar("--danger"),
    dim:     cssVar("--text-dim"),
  };
}

function destroyChart(key) {
  if (charts[key]) { charts[key].destroy(); charts[key] = null; }
}

/* ─── Stats numéricos ─────────────────────────────────────────── */
function pintarStats(data) {
  const set = (key, val) => {
    const el = document.querySelector(`[data-stat="${key}"]`);
    if (!el) return;
    el.textContent = val;
  };
  set("total_tareas",        data.resumen.total_tareas);
  set("proximas_7_dias",     data.resumen.proximas_7_dias);
  set("vencidas_pendientes", data.resumen.vencidas_pendientes);
  set(
    "tasa",
    data.puntualidad.tasa == null ? "—" : `${data.puntualidad.tasa}%`
  );
}

/* ─── Gráficos ────────────────────────────────────────────────── */
function pintarEstado(porEstado) {
  const ctx = document.querySelector('[data-chart="estado"]');
  if (!ctx) return;
  destroyChart("estado");
  const p = paleta();

  charts.estado = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Pendiente", "En progreso", "Completada"],
      datasets: [{
        data: [porEstado.pendiente, porEstado.en_progreso, porEstado.completada],
        backgroundColor: [p.dim, p.accent, p.success],
        borderColor: cssVar("--surface"),
        borderWidth: 2,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "65%",
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: p.text, boxWidth: 10, font: { size: 12 }, padding: 12 },
        },
      },
    },
  });
}

function pintarPrioridad(porPrioridad) {
  const ctx = document.querySelector('[data-chart="prioridad"]');
  if (!ctx) return;
  destroyChart("prioridad");
  const p = paleta();

  charts.prioridad = new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["Baja", "Media", "Alta", "Crítica"],
      datasets: [{
        data: [porPrioridad.baja, porPrioridad.media, porPrioridad.alta, porPrioridad.critica],
        backgroundColor: [p.success, p.dim, p.warning, p.danger],
        borderRadius: 4,
        borderSkipped: false,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: { ticks: { color: p.text }, grid: { display: false } },
        y: {
          beginAtZero: true,
          ticks: { color: p.text, precision: 0 },
          grid: { color: p.border },
        },
      },
    },
  });
}

function pintarSerie(serie) {
  const ctx = document.querySelector('[data-chart="serie"]');
  if (!ctx) return;
  destroyChart("serie");
  const p = paleta();

  charts.serie = new Chart(ctx, {
    type: "line",
    data: {
      labels: serie.map(d => d.fecha.slice(5)), // MM-DD
      datasets: [{
        data: serie.map(d => d.completadas),
        borderColor: p.accent,
        backgroundColor: p.accent + "22",
        borderWidth: 2,
        fill: true,
        tension: 0.3,
        pointBackgroundColor: p.accent,
        pointRadius: 4,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: p.text }, grid: { display: false } },
        y: {
          beginAtZero: true,
          ticks: { color: p.text, precision: 0 },
          grid: { color: p.border },
        },
      },
    },
  });
}

/* ─── Fetch + render global ───────────────────────────────────── */
export async function refrescarDashboard() {
  try {
    const data = await apiFetch("/dashboard");
    pintarStats(data);
    pintarEstado(data.resumen.por_estado);
    pintarPrioridad(data.resumen.por_prioridad);
    pintarSerie(data.serie_diaria);
  } catch (err) {
    toast(err.message, "error");
  }
}

/* ─── Init ────────────────────────────────────────────────────── */
let inicializado = false;

export function initDashboard() {
  if (inicializado) return;
  inicializado = true;

  document.addEventListener("view:changed", (e) => {
    if (e.detail.view === "dashboard") refrescarDashboard();
  });

  // Re-pinta si cambia el tema (los colores de los gráficos dependen del CSS)
  document.addEventListener("click", (e) => {
    if (e.target.closest("[data-theme-toggle]")) {
      setTimeout(refrescarDashboard, 50);
    }
  });
}
